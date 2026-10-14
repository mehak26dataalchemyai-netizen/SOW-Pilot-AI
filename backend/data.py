import os
import json
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional

from database import (
    get_db_connection,
    init_db,
    is_email_processed_db,
    mark_email_as_processed_db,
    get_db_workers
)

# Initialize database on startup
init_db()

db_lock = threading.Lock()
migration_thread_lock = threading.Lock()
migration_in_progress = False

def load_db() -> Dict[str, Any]:
    """Compatibility method returning in-memory representation of SQLite db."""
    projects = get_all_projects()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM processed_emails")
    email_cnt = cursor.fetchone()[0] + 5 # Base simulated count
    
    cursor.execute("SELECT message_id FROM processed_emails")
    msg_ids = [r["message_id"] for r in cursor.fetchall()]
    conn.close()
    
    return {
        "projects": projects,
        "emails_received_count": email_cnt,
        "processed_email_ids": msg_ids
    }

def save_db(db_data: Dict[str, Any]) -> None:
    """Compatibility method to save back any external modifications to SQLite."""
    projects = db_data.get("projects", [])
    for p in projects:
        add_project_to_sqlite(p)

def add_project_to_sqlite(p: Dict[str, Any]) -> None:
    """Direct helper to upsert a project record in the SQL database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    overview = p.get("project_overview") or {}
    proj_name = overview.get("project_name") or p.get("project_name", "Unknown")
    client = overview.get("client") or p.get("client", "Unknown")
    
    budget_val = p.get("budget", {})
    budget_amount = 0.0
    if isinstance(budget_val, dict):
        budget_amount = budget_val.get("total_cost", 0.0)
    elif isinstance(budget_val, (int, float)):
        budget_amount = float(budget_val)
    elif isinstance(budget_val, str):
        try:
            budget_amount = float(budget_val.replace("$", "").replace(",", "").strip())
        except ValueError:
            budget_amount = 0.0

    # Prefer the budget the client actually stated in the SOW document; only fall back to our own
    # calculated estimate if the document never mentioned one.
    client_budget = overview.get("client_stated_budget")
    if client_budget and client_budget not in ("Not specified", "Not Specified"):
        target_budget = client_budget
    else:
        target_budget = overview.get("budget") or p.get("target_budget", "Not Specified")
    readiness_score = p.get("overall_readiness_score", 0)
    approved = 1 if p.get("budget_approved") else 0
    processed_at = p.get("processed_at") or datetime.now().strftime("%b %d, %Y %I:%M %p")
    
    # Generate unique ID if not present
    p_id = p.get("id")
    if not p_id:
        p_id = f"{proj_name.lower().replace(' ', '_')}_{client.lower().replace(' ', '_')}"
        p["id"] = p_id

    # Check if exists
    cursor.execute("SELECT 1 FROM projects WHERE id = ?", (p_id,))
    exists = cursor.fetchone() is not None
    
    if exists:
        cursor.execute("""
            UPDATE projects SET 
                project_name = ?,
                client = ?,
                budget = ?,
                target_budget = ?,
                readiness_score = ?,
                budget_approved = ?,
                processed_at = ?,
                full_data = ?
            WHERE id = ?
        """, (proj_name, client, budget_amount, target_budget, readiness_score, approved, processed_at, json.dumps(p), p_id))
    else:
        cursor.execute("""
            INSERT INTO projects (id, project_name, client, budget, target_budget, readiness_score, budget_approved, processed_at, full_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (p_id, proj_name, client, budget_amount, target_budget, readiness_score, approved, processed_at, json.dumps(p)))
        
    conn.commit()
    conn.close()

def is_email_processed(message_id: str) -> bool:
    """Check if the given email Message-ID has already been ingested in SQLite."""
    return is_email_processed_db(message_id)

def mark_email_as_processed(message_id: str) -> None:
    """Register the given email Message-ID as processed to avoid duplicates in SQLite."""
    mark_email_as_processed_db(message_id)

def get_all_projects() -> List[Dict[str, Any]]:
    """Retrieve all projects from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_data FROM projects ORDER BY processed_at ASC")
    rows = cursor.fetchall()
    conn.close()
    
    projects = []
    for r in rows:
        try:
            p = json.loads(r["full_data"])
            projects.append(p)
        except Exception:
            pass
    return projects

def get_latest_project() -> Optional[Dict[str, Any]]:
    """Retrieve the most recently processed project."""
    projects = get_all_projects()
    if not projects:
        return None
    return projects[-1]

def index_project_in_vector_store(p: Dict[str, Any]) -> None:
    """Helper to parse a project record and index its requirements in the RAG database."""
    try:
        from retriever import PersistentVectorStore
        overview = p.get("project_overview") or {}
        proj_name = overview.get("project_name") or p.get("project_name", "Unknown")
        client = overview.get("client", "Unknown")
        tech_sum = p.get("technology_summary") or {}
        stack = tech_sum.get("stack", [])
        deliverables = tech_sum.get("deliverables", [])
        summary = p.get("executive_summary", "")
        risks_list = [r.get("risk_name", "") if isinstance(r, dict) else str(r) for r in p.get("risks", [])]
        
        req_text = f"Project SOW: {proj_name}. Client Partner: {client}. Summary: {summary}. " \
                   f"Competencies and Stack: {', '.join(stack)}. " \
                   f"Deliverables: {'; '.join(deliverables)}. " \
                   f"Delivery Risks: {'; '.join(risks_list)}."
                   
        store = PersistentVectorStore()
        store.add_document("sow_requirements", proj_name, req_text, {"project_name": proj_name})
        print(f"[VECTOR STORE] Indexed project requirements for: {proj_name}")
    except Exception as e:
        print(f"[VECTOR STORE ERROR] Failed to index SOW project requirements: {e}")

def add_project(project: Dict[str, Any], raw_sow_text: str = None) -> None:
    """Add a new project to the database and increment received email count.

    raw_sow_text (the original source document, when available) is passed through to the compliance
    engine for the real extraction-faithfulness check — it compares the extracted output against the
    actual source text, not against itself."""
    add_project_to_sqlite(project)

    # Track metrics in database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM processed_emails")
    email_cnt = cursor.fetchone()[0]
    conn.close()

    # Run compliance and audit logs
    try:
        from compliance import evaluate_and_audit_project
        evaluate_and_audit_project(project, raw_sow_text)
    except Exception as e:
        print(f"[COMPLIANCE ERROR] Failed to run compliance engine: {e}")
        
    # Index requirements in RAG database
    index_project_in_vector_store(project)

def get_dashboard_stats() -> Dict[str, Any]:
    """Compute statistics for dashboard visualization using the database."""
    projects = get_all_projects()
    projects_processed = len(projects)
    
    # Fetch email counts from database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM processed_emails")
    emails_received = cursor.fetchone()[0] + 5 # Base simulated count
    conn.close()
    
    total_budget = 0
    total_resources = 0
    total_duration_weeks = 0
    
    for p in projects:
        # Budget
        budget_info = p.get("budget", {})
        total_cost = 0
        if isinstance(budget_info, dict):
            total_cost = budget_info.get("total_cost", 0)
        elif isinstance(budget_info, (int, float)):
            total_cost = budget_info
        elif isinstance(budget_info, str):
            try:
                clean_str = budget_info.replace("$", "").replace(",", "").strip()
                total_cost = float(clean_str)
            except ValueError:
                total_cost = 0
        total_budget += total_cost
        
        # Resources
        res_info = p.get("resource_plan", {})
        team = res_info.get("recommended_team", [])
        if isinstance(team, list):
            for member in team:
                if isinstance(member, dict):
                    total_resources += member.get("count", 1)
                else:
                    total_resources += 1
        elif isinstance(res_info.get("total_resources"), (int, float)):
            total_resources += res_info.get("total_resources")
            
        # Duration
        dur = p.get("project_overview", {}).get("duration", "")
        weeks = 12
        if "week" in dur.lower():
            try:
                weeks = int(''.join(filter(str.isdigit, dur)))
            except ValueError:
                pass
        elif "month" in dur.lower():
            try:
                months = int(''.join(filter(str.isdigit, dur)))
                weeks = months * 4
            except ValueError:
                pass
        total_duration_weeks += weeks

    avg_duration = round(total_duration_weeks / projects_processed) if projects_processed > 0 else 0
    ai_agents_executed = projects_processed * 6

    # Return dashboard stats structure
    return {
        "projects_processed": projects_processed,
        "emails_received": emails_received,
        "ai_agents_executed": ai_agents_executed,
        "estimated_budget": total_budget,
        "total_resources": total_resources,
        "project_duration_weeks": avg_duration,
        "recent_projects": [
            {
                "project_name": p.get("project_overview", {}).get("project_name", "Unknown"),
                "client": p.get("project_overview", {}).get("client", "Unknown"),
                "budget": p.get("budget", {}).get("total_cost", 0) if isinstance(p.get("budget"), dict) else p.get("budget", 0),
                "target_budget": p.get("project_overview", {}).get("client_stated_budget") or "Not Specified",
                "readiness_score": p.get("overall_readiness_score", 0),
                "processed_at": p.get("processed_at", "Just now")
            }
            for p in reversed(projects)
        ]
    }

def get_project_by_name(project_name: str) -> Optional[Dict[str, Any]]:
    """Finds a project's full stored payload by name, checking the indexed column first
    then falling back to a scan (covers projects whose column wasn't populated on import)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_data FROM projects WHERE project_name = ?", (project_name,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("SELECT full_data FROM projects")
        for r in cursor.fetchall():
            p_data = json.loads(r["full_data"])
            p_name = p_data.get("project_overview", {}).get("project_name") or p_data.get("project_name")
            if p_name == project_name:
                conn.close()
                return p_data
        conn.close()
        return None
    conn.close()
    return json.loads(row["full_data"])

def set_outbound_message_id(project_name: str, message_id: str, field_key: str = "last_outbound_message_id") -> bool:
    """Records the Message-ID we set on an email we just sent for this project, so a later
    'fetch from mail' action knows which thread to search for a reply in. field_key lets different
    outbound messages (pre-bid questions vs. the proposal) be tracked separately under distinct keys —
    sharing one key would mean sending the proposal silently breaks the pre-bid fetch-answers feature,
    since that would start searching for a reply to the proposal instead of the pre-bid questions."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, full_data FROM projects WHERE project_name = ?", (project_name,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("SELECT id, full_data FROM projects")
        for r in cursor.fetchall():
            p_data = json.loads(r["full_data"])
            p_name = p_data.get("project_overview", {}).get("project_name") or p_data.get("project_name")
            if p_name == project_name:
                row = r
                break

    if not row:
        conn.close()
        return False

    p_id = row["id"]
    p_data = json.loads(row["full_data"])
    if not isinstance(p_data.get("email_metadata"), dict):
        p_data["email_metadata"] = {}
    p_data["email_metadata"][field_key] = message_id
    p_data["email_metadata"][field_key.replace("_message_id", "_sent_at")] = datetime.now().strftime("%b %d, %Y %I:%M %p")

    cursor.execute("UPDATE projects SET full_data = ? WHERE id = ?", (json.dumps(p_data), p_id))
    conn.commit()
    conn.close()
    return True

def apply_price_adjustment(project_name: str, adjustment_percent: float, reason: str) -> Optional[Dict[str, Any]]:
    """Applies a stakeholder-driven price adjustment (e.g. Finance's '+3% for Net-90 cost-of-money')
    directly to the stored budget — so an approval resolution actually moves the number instead of
    sitting in a free-text note nobody re-reads. Every adjustment is appended to a running log, never
    overwriting prior ones, so the final price is always traceable back to who asked for what."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, full_data FROM projects WHERE project_name = ?", (project_name,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("SELECT id, full_data FROM projects")
        for r in cursor.fetchall():
            p_data = json.loads(r["full_data"])
            p_name = p_data.get("project_overview", {}).get("project_name") or p_data.get("project_name")
            if p_name == project_name:
                row = r
                break

    if not row:
        conn.close()
        return None

    p_id = row["id"]
    p_data = json.loads(row["full_data"])
    budget = p_data.get("budget")
    if not isinstance(budget, dict):
        conn.close()
        return None

    base_price = budget.get("bid_price") or budget.get("total_cost") or 0.0
    delta = round(base_price * (adjustment_percent / 100.0), 2)
    new_price = round(base_price + delta, 2)

    adjustments = budget.get("price_adjustments", [])
    if not isinstance(adjustments, list):
        adjustments = []
    adjustments.append({
        "adjustment_percent": adjustment_percent,
        "delta_amount": delta,
        "reason": reason,
        "applied_at": datetime.now().strftime("%b %d, %Y %I:%M %p")
    })

    budget["price_adjustments"] = adjustments
    budget["bid_price"] = new_price
    p_data["budget"] = budget
    if isinstance(p_data.get("project_overview"), dict):
        p_data["project_overview"]["budget"] = f"${new_price:,.0f}"

    cursor.execute(
        "UPDATE projects SET budget = ?, full_data = ? WHERE id = ?",
        (new_price, json.dumps(p_data), p_id)
    )
    conn.commit()
    conn.close()
    return budget

def apply_cost_delta(project_name: str, delta_amount: float, reason: str) -> Optional[Dict[str, Any]]:
    """Applies a raw-dollar cost change directly to the stored bid price — the amount-based sibling to
    apply_price_adjustment's percent-based version, used when a schedule disruption's real cost impact
    has already been computed deterministically (e.g. the labor/infra cost delta from a timeline shift)
    rather than expressed as a percentage. Writes to the SAME price_adjustments log, so a project's full
    financial history — negotiated discounts, stakeholder premiums, and timeline-driven cost impacts —
    reads as one unified, traceable record instead of three separate things."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, full_data FROM projects WHERE project_name = ?", (project_name,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("SELECT id, full_data FROM projects")
        for r in cursor.fetchall():
            p_data = json.loads(r["full_data"])
            p_name = p_data.get("project_overview", {}).get("project_name") or p_data.get("project_name")
            if p_name == project_name:
                row = r
                break

    if not row:
        conn.close()
        return None

    p_id = row["id"]
    p_data = json.loads(row["full_data"])
    budget = p_data.get("budget")
    if not isinstance(budget, dict):
        conn.close()
        return None

    base_price = budget.get("bid_price") or budget.get("total_cost") or 0.0
    delta = round(delta_amount, 2)
    new_price = round(base_price + delta, 2)

    adjustments = budget.get("price_adjustments", [])
    if not isinstance(adjustments, list):
        adjustments = []
    adjustments.append({
        "adjustment_percent": None,
        "delta_amount": delta,
        "reason": reason,
        "applied_at": datetime.now().strftime("%b %d, %Y %I:%M %p")
    })

    budget["price_adjustments"] = adjustments
    budget["bid_price"] = new_price
    p_data["budget"] = budget
    if isinstance(p_data.get("project_overview"), dict):
        p_data["project_overview"]["budget"] = f"${new_price:,.0f}"

    cursor.execute(
        "UPDATE projects SET budget = ?, full_data = ? WHERE id = ?",
        (new_price, json.dumps(p_data), p_id)
    )
    conn.commit()
    conn.close()
    return budget

def update_project_approval(project_name: str, approved: bool) -> bool:
    """Updates the budget approval status of a project in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find matching project ID first
    cursor.execute("SELECT id, full_data FROM projects WHERE project_name = ?", (project_name,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("SELECT id, full_data FROM projects")
        for r in cursor.fetchall():
            p_data = json.loads(r["full_data"])
            p_name = p_data.get("project_overview", {}).get("project_name") or p_data.get("project_name")
            if p_name == project_name:
                row = r
                break
                
    if not row:
        conn.close()
        return False
        
    p_id = row["id"]
    p_data = json.loads(row["full_data"])
    p_data["budget_approved"] = approved
    
    cursor.execute(
        "UPDATE projects SET budget_approved = ?, full_data = ? WHERE id = ?",
        (1 if approved else 0, json.dumps(p_data), p_id)
    )
    conn.commit()
    conn.close()
    return True

def backfill_missing_requirement_versions() -> None:
    """Projects ingested before the requirement_versions table existed have no requirements_v1
    snapshot — which breaks Pre-Bid Q&A generation and Approval routing, since both read reqs_v1
    directly and refuse to run without it ("Requirements v1 must exist first"). Reconstructs a
    reqs-shaped dict from the project's own already-stored fields (no LLM call, no re-ingestion)
    and backfills it once per project that's missing one. Fields that were never persisted outside
    the original ephemeral extraction (none for this project shape) simply come back empty rather
    than invented."""
    from database import get_requirement_version, save_requirement_version

    for p in get_all_projects():
        overview = p.get("project_overview")
        if not isinstance(overview, dict):
            overview = {}
        proj_name = overview.get("project_name") or p.get("project_name")
        if not proj_name or get_requirement_version(proj_name, 1):
            continue

        tech_sum = p.get("technology_summary")
        if not isinstance(tech_sum, dict):
            tech_sum = {}
        bid_details = p.get("bid_details")
        if not isinstance(bid_details, dict):
            bid_details = {}

        reqs = {
            "project_name": proj_name,
            "client": overview.get("client", ""),
            "duration": overview.get("duration", ""),
            "summary": p.get("executive_summary", ""),
            "tech_stack": tech_sum.get("stack", []),
            "deliverables": tech_sum.get("deliverables", []),
            "constraints": tech_sum.get("constraints", []),
            "dependencies": tech_sum.get("dependencies", []),
            "submission_deadline": bid_details.get("submission_deadline"),
            "pre_bid_question_deadline": bid_details.get("pre_bid_question_deadline"),
            "required_certifications": bid_details.get("required_certifications", []),
            "required_bid_documents": bid_details.get("required_bid_documents", []),
            "evaluation_criteria": bid_details.get("evaluation_criteria", []),
        }
        try:
            save_requirement_version(proj_name, 1, reqs)
            print(f"[MIGRATION] Backfilled requirements_v1 for: {proj_name}")
        except Exception as e:
            print(f"[MIGRATION ERROR] Failed to backfill requirements_v1 for {proj_name}: {e}")

def migrate_empty_budgets() -> None:
    """Recalculates budgets, risks, recommendations, and readiness scores for incomplete projects."""
    global migration_in_progress
    with migration_thread_lock:
        if migration_in_progress:
            return
        migration_in_progress = True

    try:
        db_projects = get_all_projects()
        updated = False
        from agents import estimate_costs, analyze_risks, generate_internal_bid_analysis
        
        for p in db_projects:
            budget = p.get("budget")
            if not isinstance(budget, dict):
                budget = {}
            recommendations = p.get("recommendations", [])
            score = p.get("overall_readiness_score", 0)
            
            is_anchored = budget.get("total_cost") in [215000, 187500, 187000]
            # Catches records corrupted by the duration-parsing bug (fixed in estimate_costs(), but
            # projects processed before the fix may still have a cost computed from a nonsense
            # duration — e.g. a descriptive "estimated_completion" sentence whose digits all got
            # concatenated into one number, producing budgets in the tens of millions to quadrillions
            # for what should be a normal few-hundred-thousand-dollar engagement). $10M is a generous
            # heuristic ceiling for this system's typical project scale, not a real business rule.
            is_absurd = isinstance(budget.get("total_cost"), (int, float)) and budget.get("total_cost") > 10_000_000
            if not budget or not budget.get("total_cost") or not recommendations or score == 0 or is_anchored or is_absurd:
                overview = p.get("project_overview")
                if not isinstance(overview, dict):
                    overview = {}
                proj_name = overview.get("project_name") or p.get("project_name", "Unknown")
                print(f"[MIGRATION] Repairing incomplete project: {proj_name}")
                
                # Reconstruct requirements dict
                tech_sum = p.get("technology_summary")
                if not isinstance(tech_sum, dict):
                    tech_sum = {}
                reqs = {
                    "project_name": proj_name,
                    "client": overview.get("client", p.get("client", "")),
                    "duration": overview.get("duration", p.get("duration", "")),
                    "tech_stack": tech_sum.get("stack", []),
                    "deliverables": tech_sum.get("deliverables", []),
                    "constraints": tech_sum.get("constraints", []),
                    "dependencies": tech_sum.get("dependencies", [])
                }
                resources = p.get("resource_plan")
                if not isinstance(resources, dict):
                    resources = {}
                timeline = p.get("timeline")
                if not isinstance(timeline, dict):
                    timeline = {}
                
                # Calculate risks first (cost's contingency buffer is risk-driven), then cost, then report
                try:
                    current_risks = p.get("risks", [])
                    if not current_risks:
                        risks_out = analyze_risks(reqs)
                    else:
                        risks_out = {"risks": current_risks}

                    costs = estimate_costs(reqs, resources, timeline, risks_out)
                    p["budget"] = costs

                    if "project_overview" not in p or not isinstance(p["project_overview"], dict):
                        p["project_overview"] = {}
                    p["project_overview"]["budget"] = f"${costs.get('total_cost', 0):,}"
                    p["project_overview"]["project_name"] = proj_name
                    p["project_overview"]["client"] = reqs["client"]
                    p["project_overview"]["duration"] = reqs["duration"]

                    rep_out = generate_internal_bid_analysis(reqs, resources, timeline, costs, risks_out)
                    
                    tech_summary = rep_out.get("technology_summary", {})
                    if not tech_summary.get("constraints"):
                        tech_summary["constraints"] = reqs.get("constraints", [])
                    if not tech_summary.get("dependencies"):
                        tech_summary["dependencies"] = reqs.get("dependencies", [])
                    p["technology_summary"] = tech_summary
    
                    risks_list = rep_out.get("risks", [])
                    if not risks_list:
                        risks_list = risks_out.get("risks", [])
                    p["risks"] = risks_list
    
                    recs = rep_out.get("recommendations", [])
                    if not recs:
                        stack_list = tech_summary.get("stack", ["React", "FastAPI"])
                        stack_str = ", ".join(stack_list[:2])
                        recs = [
                            f"Establish core {stack_str} architectural scaffolding in Week 1 to validate event streaming.",
                            "Request AWS VPC access keys and credential profiles during kickoff to prevent deployment blocks.",
                            "Implement local caching and rate-limiting rules for API integrations to maintain performance."
                        ]
                    p["recommendations"] = recs
                    p["overall_readiness_score"] = rep_out.get("overall_readiness_score", 80)
                    
                    add_project_to_sqlite(p)
                    updated = True
                except Exception as e:
                    print(f"[MIGRATION ERROR] Failed to repair project: {e}")
    finally:
        with migration_thread_lock:
            migration_in_progress = False

def deduplicate_projects() -> None:
    """Removes duplicate projects from database, keeping only the latest version."""
    global migration_in_progress
    with migration_thread_lock:
        if migration_in_progress:
            return
        migration_in_progress = True

    try:
        db_projects = get_all_projects()
        seen_names = set()
        unique_projects = []
        
        for p in reversed(db_projects):
            p_name = p.get("project_overview", {}).get("project_name") if isinstance(p.get("project_overview"), dict) else None
            if not p_name:
                p_name = p.get("project_name", "Unknown")
                
            p_name_lower = p_name.strip().lower()
            if p_name_lower not in seen_names:
                seen_names.add(p_name_lower)
                unique_projects.append(p)
        
        unique_projects.reverse()
        
        # Rewrite to sqlite
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if length matches, if not clear and rewrite
        if len(db_projects) != len(unique_projects):
            cursor.execute("DELETE FROM projects")
            conn.commit()
            conn.close()
            
            for p in unique_projects:
                add_project_to_sqlite(p)
                index_project_in_vector_store(p)
        else:
            conn.close()
            for p in unique_projects:
                index_project_in_vector_store(p)
    finally:
        with migration_thread_lock:
            migration_in_progress = False
