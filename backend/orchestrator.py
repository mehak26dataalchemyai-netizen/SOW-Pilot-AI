import asyncio
from typing import Dict, Any, TypedDict, List, AsyncGenerator
import json
from datetime import datetime

from langgraph.graph import StateGraph, END
from agents import (
    extract_requirements,
    allocate_resources,
    plan_timeline,
    estimate_costs,
    analyze_risks,
    generate_internal_bid_analysis,
    generate_client_proposal,
    generate_architecture_proposal,
    compute_simulation_status
)

# 1. State Definition
class AgentState(TypedDict):
    pdf_text: str
    requirements: Dict[str, Any]
    resources: Dict[str, Any]
    timeline: Dict[str, Any]
    costs: Dict[str, Any]
    risks: Dict[str, Any]
    executive_report: Dict[str, Any]
    client_proposal: Dict[str, Any]
    architecture_proposal: Dict[str, Any]

# 2. Graph Nodes
def extract_node(state: AgentState) -> Dict[str, Any]:
    req = extract_requirements(state["pdf_text"])
    return {"requirements": req}

def resource_node(state: AgentState) -> Dict[str, Any]:
    res = allocate_resources(state["requirements"])
    return {"resources": res}

def timeline_node(state: AgentState) -> Dict[str, Any]:
    time = plan_timeline(state["requirements"], state["resources"])
    return {"timeline": time}

def cost_node(state: AgentState) -> Dict[str, Any]:
    c = estimate_costs(state["requirements"], state["resources"], state["timeline"], state["risks"])
    return {"costs": c}

def risk_node(state: AgentState) -> Dict[str, Any]:
    r = analyze_risks(state["requirements"])
    return {"risks": r}

def architecture_node(state: AgentState) -> Dict[str, Any]:
    a = generate_architecture_proposal(state["requirements"])
    return {"architecture_proposal": a}

def report_node(state: AgentState) -> Dict[str, Any]:
    rep = generate_internal_bid_analysis(
        state["requirements"],
        state["resources"],
        state["timeline"],
        state["costs"],
        state["risks"]
    )
    return {"executive_report": rep}

def proposal_node(state: AgentState) -> Dict[str, Any]:
    prop = generate_client_proposal(
        state["requirements"],
        state["resources"],
        state["timeline"],
        state["costs"],
        state["risks"]
    )
    return {"client_proposal": prop}

# 3. Compile LangGraph Workflow
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("extract", extract_node)
workflow.add_node("resources", resource_node)
workflow.add_node("timeline", timeline_node)
workflow.add_node("costs", cost_node)
workflow.add_node("risks", risk_node)
workflow.add_node("architecture", architecture_node)
workflow.add_node("report", report_node)
workflow.add_node("proposal", proposal_node)

# Add edges. Resources must complete before timeline, since phase durations are grounded in the
# actual assigned headcount. Risks and architecture run in parallel with resources/timeline (they only
# need requirements). Costs waits on resources, timeline, AND risks, since the contingency buffer is risk-driven.
workflow.set_entry_point("extract")
workflow.add_edge("extract", "resources")
workflow.add_edge("extract", "risks")
workflow.add_edge("extract", "architecture")
workflow.add_edge("resources", "timeline")

workflow.add_edge("resources", "costs")
workflow.add_edge("timeline", "costs")
workflow.add_edge("risks", "costs")

workflow.add_edge("costs", "report")
workflow.add_edge("architecture", "report")
workflow.add_edge("report", "proposal")

workflow.add_edge("proposal", END)

orchestrator_graph = workflow.compile()

# 4. Asynchronous Visual Execution Stream
async def run_visual_orchestrator(pdf_text: str) -> AsyncGenerator[str, None]:
    """
    Executes the LangGraph orchestrator step-by-step, running planning nodes in parallel.
    Yields JSON-formatted SSE events detailing progress and sub-steps for the UI.
    """
    state: AgentState = {
        "pdf_text": pdf_text,
        "requirements": {},
        "resources": {},
        "timeline": {},
        "costs": {},
        "risks": {},
        "executive_report": {}
    }

    try:
        # --- AGENT 1: Extraction ---
        yield sse_event("Requirement Extraction Agent", "running", 15, "Reading SOW PDF document...")
        await asyncio.sleep(1.0)
        yield sse_event("Requirement Extraction Agent", "running", 50, "Extracting project scope & technologies...")
        await asyncio.sleep(1.0)
        yield sse_event("Requirement Extraction Agent", "running", 80, "Generating executive summary draft...")
        
        # Run extraction in a separate thread to prevent blocking the event loop
        loop = asyncio.get_running_loop()
        req_result = await loop.run_in_executor(None, extract_requirements, pdf_text)
        state["requirements"] = req_result
        
        yield sse_event("Requirement Extraction Agent", "completed", 100, "Successfully extracted project properties.", req_result)
        if req_result.get("_simulated"):
            yield sse_event("Requirement Extraction Agent", "warning", 100, "AI call failed — showing offline placeholder data, not a real analysis.")

        # Persist requirements_v1 as an immutable snapshot (pre-bid Q&A later produces v2, never overwriting this)
        proj_name_for_versioning = req_result.get("project_name")
        if proj_name_for_versioning:
            try:
                from database import save_requirement_version
                await loop.run_in_executor(None, save_requirement_version, proj_name_for_versioning, 1, req_result)
            except Exception as e:
                print(f"[REQUIREMENTS VERSIONING] Failed to save v1 snapshot: {e}")
        await asyncio.sleep(0.8)

        # --- PHASE 1a: Resources, Risks & Architecture (Parallel — all only need requirements) ---
        yield sse_event("Resource Allocation Agent", "running", 10, "Queueing resource allocation planning...")
        yield sse_event("Risk Analysis Agent", "running", 10, "Queueing delivery risk analysis...")
        yield sse_event("Architecture Proposal Agent", "running", 10, "Queueing solution architecture design...")
        await asyncio.sleep(0.8)

        yield sse_event("Resource Allocation Agent", "running", 50, "Matching SOW stack to engineer skill matrices...")
        yield sse_event("Risk Analysis Agent", "running", 50, "Assessing hiring timelines & external dependencies...")
        yield sse_event("Architecture Proposal Agent", "running", 50, "Designing components and data flow...")
        await asyncio.sleep(1.2)

        yield sse_event("Resource Allocation Agent", "running", 85, "Estimating team sizes and hiring requisitions...")
        yield sse_event("Risk Analysis Agent", "running", 85, "Compiling severity risk matrix and mitigations...")
        yield sse_event("Architecture Proposal Agent", "running", 85, "Finalizing integration points and design decisions...")

        async def run_res():
            return await loop.run_in_executor(None, allocate_resources, state["requirements"])
        async def run_risk():
            return await loop.run_in_executor(None, analyze_risks, state["requirements"])
        async def run_arch():
            return await loop.run_in_executor(None, generate_architecture_proposal, state["requirements"])

        res_task = asyncio.create_task(run_res())
        risk_task = asyncio.create_task(run_risk())
        arch_task = asyncio.create_task(run_arch())

        res_out, risk_out, arch_out = await asyncio.gather(res_task, risk_task, arch_task)
        state["resources"] = res_out
        state["risks"] = risk_out
        state["architecture_proposal"] = arch_out

        yield sse_event("Resource Allocation Agent", "completed", 100, "Determined resource team & skill matrix.", res_out)
        yield sse_event("Risk Analysis Agent", "completed", 100, "Generated project delivery risk matrices.", risk_out)
        yield sse_event("Architecture Proposal Agent", "completed", 100, "Solution architecture proposal drafted.", arch_out)
        for label, out in [("Resource Allocation Agent", res_out), ("Risk Analysis Agent", risk_out), ("Architecture Proposal Agent", arch_out)]:
            if out.get("_simulated"):
                yield sse_event(label, "warning", 100, "AI call failed — showing offline placeholder data, not a real analysis.")
        await asyncio.sleep(0.5)

        # --- PHASE 1b: Timeline Planning (needs the actual assigned team from Resources above) ---
        yield sse_event("Timeline Planning Agent", "running", 15, "Grounding phase durations in the assigned delivery team...")
        await asyncio.sleep(0.8)
        yield sse_event("Timeline Planning Agent", "running", 60, "Structuring project phases and milestones...")

        time_out = await loop.run_in_executor(None, plan_timeline, state["requirements"], state["resources"])
        state["timeline"] = time_out

        yield sse_event("Timeline Planning Agent", "completed", 100, "Finalized phase schedules & sprint tasks.", time_out)
        if time_out.get("_simulated"):
            yield sse_event("Timeline Planning Agent", "warning", 100, "AI call failed — showing offline placeholder data, not a real analysis.")
        await asyncio.sleep(0.5)

        # --- PHASE 2: Cost & Budget Calculation (needs resources, timeline, AND risks for the contingency buffer) ---
        yield sse_event("Cost Estimation Agent", "running", 25, "Initiating cost calculation based on team size & timeline...")
        await asyncio.sleep(0.8)
        yield sse_event("Cost Estimation Agent", "running", 75, "Summing developer rates, software licenses, and risk-weighted contingency...")

        cost_out = await loop.run_in_executor(None, estimate_costs, state["requirements"], state["resources"], state["timeline"], state["risks"])
        state["costs"] = cost_out
        
        yield sse_event("Cost Estimation Agent", "completed", 100, "Calculated full project budget breakdown.", cost_out)
        if cost_out.get("_simulated"):
            yield sse_event("Cost Estimation Agent", "warning", 100, "AI call failed — showing a formula-based fallback estimate, not an AI-generated analysis.")
        await asyncio.sleep(1.0)

        # --- AGENT 6: Internal Bid Analysis (technical detail, margins, risk reasoning — internal only) ---
        yield sse_event("Internal Bid Analysis Agent", "running", 20, "Synthesizing timeline, resource, cost, and risk reports...")
        await asyncio.sleep(0.8)
        yield sse_event("Internal Bid Analysis Agent", "running", 60, "Computing readiness score and drafting internal recommendations...")
        await asyncio.sleep(0.8)
        yield sse_event("Internal Bid Analysis Agent", "running", 90, "Writing final internal delivery document payload...")

        rep_result = await loop.run_in_executor(
            None,
            generate_internal_bid_analysis,
            state["requirements"],
            state["resources"],
            state["timeline"],
            state["costs"],
            state["risks"]
        )
        state["executive_report"] = rep_result

        yield sse_event("Internal Bid Analysis Agent", "completed", 100, "Internal bid analysis generated.", rep_result)
        if rep_result.get("_simulated"):
            yield sse_event("Internal Bid Analysis Agent", "warning", 100, "AI call failed — showing offline placeholder data, not a real analysis.")
        await asyncio.sleep(0.5)

        # --- AGENT 7: Client-Facing Proposal (a separate, persuasive document — not a copy of the RFP) ---
        yield sse_event("Client Proposal Agent", "running", 30, "Drafting client-facing response weighted to their evaluation criteria...")
        await asyncio.sleep(0.8)
        yield sse_event("Client Proposal Agent", "running", 80, "Finalizing proposal narrative and next steps...")

        proposal_result = await loop.run_in_executor(
            None,
            generate_client_proposal,
            state["requirements"],
            state["resources"],
            state["timeline"],
            state["costs"],
            state["risks"]
        )

        yield sse_event("Client Proposal Agent", "completed", 100, "Client-facing proposal drafted.", proposal_result)
        if proposal_result.get("_simulated"):
            yield sse_event("Client Proposal Agent", "warning", 100, "AI call failed — showing offline placeholder text, not a real proposal.")
        await asyncio.sleep(0.5)

        # Merge and validate technology_summary, risks, and recommendations fallback
        tech_summary = rep_result.get("technology_summary", {})
        if not tech_summary.get("constraints"):
            tech_summary["constraints"] = state["requirements"].get("constraints", [])
        if not tech_summary.get("dependencies"):
            tech_summary["dependencies"] = state["requirements"].get("dependencies", [])

        risks_list = rep_result.get("risks", [])
        if not risks_list:
            if isinstance(state["risks"], dict):
                risks_list = state["risks"].get("risks", [])
            elif isinstance(state["risks"], list):
                risks_list = state["risks"]

        recs = rep_result.get("recommendations", [])
        if not recs:
            stack_list = tech_summary.get("stack", ["React", "FastAPI"])
            stack_str = ", ".join(stack_list[:2])
            recs = [
                f"Establish core {stack_str} architectural scaffolding in Week 1 to validate event streaming.",
                "Request AWS VPC access keys and credential profiles during kickoff to prevent deployment blocks.",
                "Implement local caching and rate-limiting rules for API integrations to maintain performance."
            ]

        sim_status = compute_simulation_status(
            state["requirements"], state["resources"], state["timeline"],
            state["costs"], state["risks"], rep_result, proposal_result, state["architecture_proposal"]
        )

        # Yield the final compiled project payload
        final_payload = {
            "project_overview": rep_result.get("project_overview", {}),
            "executive_summary": rep_result.get("executive_summary", ""),
            "technology_summary": tech_summary,
            "resource_plan": rep_result.get("resource_plan", {}),
            "timeline": rep_result.get("timeline", {}),
            "budget": rep_result.get("budget", {}),
            "architecture_proposal": state["architecture_proposal"],
            "client_proposal": proposal_result,
            "bid_details": {
                "submission_deadline": state["requirements"].get("submission_deadline"),
                "pre_bid_question_deadline": state["requirements"].get("pre_bid_question_deadline"),
                "required_certifications": state["requirements"].get("required_certifications", []),
                "required_bid_documents": state["requirements"].get("required_bid_documents", []),
                "evaluation_criteria": state["requirements"].get("evaluation_criteria", [])
            },
            "risks": risks_list,
            "recommendations": recs,
            "overall_readiness_score": rep_result.get("overall_readiness_score", 80),
            "processed_at": datetime.now().strftime("%b %d, %Y %I:%M %p"),
            "is_simulated": sim_status["is_simulated"],
            "simulation_notice": sim_status["simulation_notice"]
        }

        yield f"data: {json.dumps({'type': 'final_result', 'data': final_payload})}\n\n"

    except Exception as err:
        print(f"Orchestration stream error: {err}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(err)})}\n\n"

def sse_event(agent: str, status: str, progress: int, message: str, data: Any = None) -> str:
    """Helper to format status changes as Server-Sent Event (SSE) strings."""
    event_data = {
        "type": "status",
        "agent": agent,
        "status": status,
        "progress": progress,
        "message": message,
        "data": data
    }
    return f"data: {json.dumps(event_data)}\n\n"
