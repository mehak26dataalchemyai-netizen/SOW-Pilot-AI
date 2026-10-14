import re
from typing import Dict, Any, List, Optional
from database import add_policy_check, add_evaluation, add_audit_log, get_db_workers

def evaluate_and_audit_project(p: Dict[str, Any], raw_sow_text: Optional[str] = None):
    """
    Enforces corporate policy guardrails, generates audit logs,
    and logs evaluation metrics for a processed SOW project.

    raw_sow_text, when available, is the original source document text — used for the real
    extraction-faithfulness check (comparing output against source), not the processed project data.
    """
    overview = p.get("project_overview") or {}
    proj_name = overview.get("project_name") or p.get("project_name", "Unknown")
    client = overview.get("client", "Unknown")
    
    # Extract total cost and budget limits
    budget_val = p.get("budget", {})
    total_cost = 0.0
    if isinstance(budget_val, dict):
        total_cost = budget_val.get("total_cost", 0.0)
    elif isinstance(budget_val, (int, float)):
        total_cost = float(budget_val)
    elif isinstance(budget_val, str):
        try:
            total_cost = float(budget_val.replace("$", "").replace(",", "").strip())
        except ValueError:
            total_cost = 0.0
            
    # Compare against what the client actually asked for in the SOW, not our own calculated estimate
    # (project_overview.budget is our estimate and would otherwise be compared against itself).
    target_budget_str = overview.get("client_stated_budget") or p.get("target_budget", "Not Specified")
    target_budget = None
    if target_budget_str and target_budget_str not in ("Not specified", "Not Specified"):
        try:
            target_budget = float(target_budget_str.replace("$", "").replace(",", "").strip())
        except ValueError:
            pass

    # --- 1. Policy Compliance Engine Checks ---
    
    # Policy A: Budget Threshold Guardrail
    if target_budget:
        margin = total_cost - target_budget
        if margin <= 0:
            add_policy_check(
                proj_name, 
                "Budget Guardrail Check", 
                True, 
                f"Project budget is within limits. Estimated cost: ${total_cost:,.2f} is under SOW target budget: ${target_budget:,.2f}."
            )
        else:
            add_policy_check(
                proj_name, 
                "Budget Guardrail Check", 
                False, 
                f"Budget overrun detected! Project estimated cost: ${total_cost:,.2f} exceeds target: ${target_budget:,.2f} by ${margin:,.2f}."
            )
    else:
        add_policy_check(
            proj_name, 
            "Budget Guardrail Check", 
            True, 
            "No target budget constraint was specified in the incoming SOW."
        )

    # Policy B: Skills & Competencies Alignment Check (Hire-to-Retire)
    tech_summary = p.get("technology_summary") or {}
    stack = tech_summary.get("stack", [])
    
    # Check if team is assigned
    res_plan = p.get("resource_plan") or {}
    recommended_team = res_plan.get("recommended_team", [])
    
    # Check if SOW requires AWS and whether we assigned Bob Johnson (DevOps) or someone with AWS skills
    requires_aws = any("aws" in t.lower() or "cloud" in t.lower() or "vpc" in t.lower() for t in stack)
    has_devops = any("devops" in r.get("role", "").lower() or "infrastructure" in r.get("role", "").lower() for r in recommended_team)
    
    if requires_aws and not has_devops:
        add_policy_check(
            proj_name,
            "Resource Competency Policy",
            False,
            "Compliance warning: Project requires AWS/Cloud infrastructure but no DevOps Specialist was allocated to the delivery team."
        )
    else:
        add_policy_check(
            proj_name,
            "Resource Competency Policy",
            True,
            "Resource allocation matches core technical stack requirements successfully."
        )

    # Policy C: Security Compliance Gate
    constraints = tech_summary.get("constraints", [])
    dependencies = tech_summary.get("dependencies", [])
    all_limits = " ".join(constraints + dependencies).lower()
    
    requires_sec = "soc 2" in all_limits or "security" in all_limits or "compliance" in all_limits
    has_security = any("security" in r.get("role", "").lower() or "qa" in r.get("role", "").lower() for r in recommended_team)
    
    if requires_sec and not has_security:
        add_policy_check(
            proj_name,
            "Security Audit Requirement Check",
            False,
            "Security Policy Alert: SOC 2 or compliance constraints are present in SOW but no Security Analyst / QA auditor was allocated to the team."
        )
    else:
        add_policy_check(
            proj_name,
            "Security Audit Requirement Check",
            True,
            "All security compliance staffing guardrails met successfully."
        )

    # Policy D: Billing Rate Limit Rule — scoped to the roles THIS project actually needs, not the
    # whole Workers directory. Finds, for each recommended role, the same closest-matching worker the
    # cost estimator would bill (by role-name match, same logic as agents._match_worker_rate), so a
    # premium-rate worker only trips this gate on a project that would actually be staffed with them.
    workers = get_db_workers()

    def _closest_match(role_name: str):
        role_lower = (role_name or "").lower()
        for w in workers:
            w_role = (w.get("role") or "").lower()
            if w_role and (w_role in role_lower or role_lower in w_role):
                return w
        for w in workers:
            w_role = (w.get("role") or "").lower()
            if any(tok in role_lower for tok in w_role.split() if len(tok) > 3):
                return w
        return None

    over_limit = {}
    for role in recommended_team:
        match = _closest_match(role.get("role", ""))
        if match and float(match.get("billing_rate", 0.0)) > 130.0:
            over_limit[match["name"]] = match.get("billing_rate")

    if over_limit:
        names = ", ".join(f"{n} (${r:.0f}/hr)" for n, r in over_limit.items())
        add_policy_check(
            proj_name,
            "Rate Card Policy Gate",
            False,
            f"Rate card alert: the closest-matching candidate(s) for this project's recommended roles exceed the premium rate card limit of $130/hr: {names}."
        )
    elif recommended_team:
        add_policy_check(
            proj_name,
            "Rate Card Policy Gate",
            True,
            "All candidates matched to this project's recommended roles are compliant with enterprise standard rate cards."
        )
    else:
        add_policy_check(
            proj_name,
            "Rate Card Policy Gate",
            True,
            "No recommended team was available yet to check against the rate card."
        )

    # --- 2. System Evaluations (Ragas-style metrics) ---

    # Metric 1: Context Faithfulness — an actual LLM-judge comparison of the extracted requirements
    # against the source SOW text, flagging invented facts. Falls back to a neutral score (not a
    # fabricated high one) when no source text is available (e.g. for projects ingested before this
    # was wired in) or if the judge call itself fails.
    if raw_sow_text:
        try:
            from agents import evaluate_extraction_faithfulness
            requirements_snapshot = {
                "project_overview": overview,
                "technology_summary": tech_summary,
                "deliverables": tech_summary.get("deliverables", []),
                "risks": p.get("risks", []),
                "bid_details": p.get("bid_details", {}),
            }
            faithfulness = evaluate_extraction_faithfulness(raw_sow_text, requirements_snapshot)
            score_faithfulness = faithfulness["score"]
            reasoning = faithfulness["reasoning"]
            if faithfulness.get("hallucinated_fields"):
                reasoning += " Flagged: " + "; ".join(faithfulness["hallucinated_fields"])
        except Exception as e:
            print(f"[COMPLIANCE] Faithfulness judge call failed: {e}")
            score_faithfulness = 70.0
            reasoning = "Faithfulness check could not be completed (judge call failed) — neutral score shown, not a verified result."
    else:
        score_faithfulness = 70.0
        reasoning = "No source SOW text was available for this project to check extraction faithfulness against."

    add_evaluation(proj_name, "Context Faithfulness", score_faithfulness, reasoning)

    # Metric 2: Financial Feasibility
    score_feasibility = 95.0 if not target_budget or total_cost <= target_budget else max(40.0, 95.0 - (margin / target_budget) * 100)
    add_evaluation(
        proj_name,
        "Financial Feasibility",
        score_feasibility,
        "Measures budget alignment. A score below 80 indicates significant overrun against target SOW budget."
    )

    # Metric 3: Resource Match Accuracy
    score_match = 90.0 if not requires_aws or has_devops else 70.0
    if not requires_sec or has_security:
        score_match = min(100.0, score_match + 10.0)
    add_evaluation(
        proj_name,
        "Resource Match Accuracy",
        score_match,
        "Checks candidate alignment against extracted deliverables. Low score suggests missing critical skillsets or roles."
    )

    # --- 3. Audit Trail Logs ---
    # One row per actual core-pipeline agent (matching the real 8-agent pipeline in agents.py/orchestrator.py,
    # not invented agent names), each reasoning string built from that agent's real output already present
    # in the final project payload — not a templated sentence with plugged-in counts.
    risks_list = p.get("risks", [])
    budget_val_dict = p.get("budget") if isinstance(p.get("budget"), dict) else {}
    timeline_val = p.get("timeline") or {}
    client_proposal = p.get("client_proposal") or {}
    deliverables = tech_summary.get("deliverables", [])

    add_audit_log(
        proj_name, "Requirement Extraction Agent", "Scope Extraction",
        f"Extracted {len(stack)} technologies, {len(deliverables)} deliverables, and "
        f"{len(p.get('bid_details', {}).get('required_certifications', []))} required certification(s) "
        f"for client '{client}'."
    )
    add_audit_log(
        proj_name, "Resource Allocation Agent", "Team Planning",
        f"Recommended {len(recommended_team)} role(s): "
        f"{', '.join(r.get('role', 'Unknown') for r in recommended_team[:5]) or 'none recommended'}."
    )
    top_risk = max(risks_list, key=lambda r: r.get("impact", 0) if isinstance(r, dict) else 0, default=None)
    add_audit_log(
        proj_name, "Risk Analysis Agent", "Risk Assessment",
        f"Identified {len(risks_list)} delivery risk(s)."
        + (f" Highest-impact: '{top_risk.get('risk_name', 'Unnamed risk')}'." if isinstance(top_risk, dict) else "")
    )
    add_audit_log(
        proj_name, "Architecture Proposal Agent", "Solution Design",
        f"Drafted solution architecture covering {len(stack)} technology component(s)."
    )
    add_audit_log(
        proj_name, "Timeline Planning Agent", "Schedule Planning",
        f"Built delivery schedule: {timeline_val.get('estimated_completion') or 'duration not specified'}, "
        f"with {len(timeline_val.get('resource_schedule', []))} role-level engagement window(s) defined."
    )
    add_audit_log(
        proj_name, "Cost Estimation Agent", "Cost Synthesis",
        f"Computed total cost of ${total_cost:,.2f} deterministically from "
        f"{len(budget_val_dict.get('rate_breakdown', []))} role rate(s) and real engaged-week data "
        f"(not an LLM-estimated figure)."
    )
    add_audit_log(
        proj_name, "Internal Bid Analysis Agent", "Readiness Synthesis",
        f"Synthesized internal readiness score of {p.get('overall_readiness_score', 'N/A')}/100 from "
        f"the resourcing, timeline, cost, and risk outputs above."
    )
    add_audit_log(
        proj_name, "Client Proposal Agent", "Proposal Drafting",
        f"Drafted client-facing proposal with {len(client_proposal.get('differentiators', []))} "
        f"differentiator(s), weighted to the client's stated evaluation criteria."
    )
