import asyncio
from typing import Dict, Any, TypedDict, List, AsyncGenerator
import json

from langgraph.graph import StateGraph, END
from agents import (
    extract_requirements,
    allocate_resources,
    plan_timeline,
    estimate_costs,
    analyze_risks,
    generate_executive_report
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

# 2. Graph Nodes
def extract_node(state: AgentState) -> Dict[str, Any]:
    req = extract_requirements(state["pdf_text"])
    return {"requirements": req}

def resource_node(state: AgentState) -> Dict[str, Any]:
    res = allocate_resources(state["requirements"])
    return {"resources": res}

def timeline_node(state: AgentState) -> Dict[str, Any]:
    time = plan_timeline(state["requirements"])
    return {"timeline": time}

def cost_node(state: AgentState) -> Dict[str, Any]:
    c = estimate_costs(state["requirements"])
    return {"costs": c}

def risk_node(state: AgentState) -> Dict[str, Any]:
    r = analyze_risks(state["requirements"])
    return {"risks": r}

def report_node(state: AgentState) -> Dict[str, Any]:
    rep = generate_executive_report(
        state["requirements"],
        state["resources"],
        state["timeline"],
        state["costs"],
        state["risks"]
    )
    return {"executive_report": rep}

# 3. Compile LangGraph Workflow
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("extract", extract_node)
workflow.add_node("resources", resource_node)
workflow.add_node("timeline", timeline_node)
workflow.add_node("costs", cost_node)
workflow.add_node("risks", risk_node)
workflow.add_node("report", report_node)

# Add edges (Requirement extraction is followed by 4 parallel nodes, then joined at report)
workflow.set_entry_point("extract")
workflow.add_edge("extract", "resources")
workflow.add_edge("extract", "timeline")
workflow.add_edge("extract", "costs")
workflow.add_edge("extract", "risks")

workflow.add_edge("resources", "report")
workflow.add_edge("timeline", "report")
workflow.add_edge("costs", "report")
workflow.add_edge("risks", "report")

workflow.add_edge("report", END)

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
        await asyncio.sleep(0.8)

        # --- PARALLEL RUNNING: Resources, Timeline, Costs, Risks ---
        yield sse_event("Resource Allocation Agent", "running", 10, "Queueing resource allocation planning...")
        yield sse_event("Timeline Planning Agent", "running", 10, "Queueing timeline scheduling...")
        yield sse_event("Cost Estimation Agent", "running", 10, "Queueing cost and budget calculations...")
        yield sse_event("Risk Analysis Agent", "running", 10, "Queueing delivery risk analysis...")
        await asyncio.sleep(0.8)

        # Run these 4 agents in parallel using asyncio.gather
        yield sse_event("Resource Allocation Agent", "running", 40, "Matching SOW stack to engineer skill matrices...")
        yield sse_event("Timeline Planning Agent", "running", 40, "Breaking down deliverables into sprint plans...")
        yield sse_event("Cost Estimation Agent", "running", 40, "Estimating developer rates & cloud resource charges...")
        yield sse_event("Risk Analysis Agent", "running", 40, "Assessing hiring timelines & external dependencies...")
        await asyncio.sleep(1.2)

        yield sse_event("Resource Allocation Agent", "running", 75, "Estimating team sizes and hiring requisitions...")
        yield sse_event("Timeline Planning Agent", "running", 75, "Structuring project phases and milestones...")
        yield sse_event("Cost Estimation Agent", "running", 75, "Summing development, infrastructure & support costs...")
        yield sse_event("Risk Analysis Agent", "running", 75, "Compiling severity risk matrix and mitigations...")
        
        # Trigger executors
        async def run_res():
            return await loop.run_in_executor(None, allocate_resources, state["requirements"])
        async def run_time():
            return await loop.run_in_executor(None, plan_timeline, state["requirements"])
        async def run_cost():
            return await loop.run_in_executor(None, estimate_costs, state["requirements"])
        async def run_risk():
            return await loop.run_in_executor(None, analyze_risks, state["requirements"])

        res_task = asyncio.create_task(run_res())
        time_task = asyncio.create_task(run_time())
        cost_task = asyncio.create_task(run_cost())
        risk_task = asyncio.create_task(run_risk())

        # Wait for all four to complete
        res_out, time_out, cost_out, risk_out = await asyncio.gather(res_task, time_task, cost_task, risk_task)
        
        state["resources"] = res_out
        state["timeline"] = time_out
        state["costs"] = cost_out
        state["risks"] = risk_out

        yield sse_event("Resource Allocation Agent", "completed", 100, "Determined resource team & skill matrix.", res_out)
        yield sse_event("Timeline Planning Agent", "completed", 100, "Finalized phase schedules & sprint tasks.", time_out)
        yield sse_event("Cost Estimation Agent", "completed", 100, "Calculated full project budget breakdown.", cost_out)
        yield sse_event("Risk Analysis Agent", "completed", 100, "Generated project delivery risk matrices.", risk_out)
        await asyncio.sleep(1.0)

        # --- AGENT 6: Executive Synthesis ---
        yield sse_event("Executive Report Agent", "running", 20, "Synthesizing timeline, resource, cost, and risk reports...")
        await asyncio.sleep(0.8)
        yield sse_event("Executive Report Agent", "running", 60, "Computing readiness score and drafting client recommendations...")
        await asyncio.sleep(0.8)
        yield sse_event("Executive Report Agent", "running", 90, "Writing final delivery document payload...")

        rep_result = await loop.run_in_executor(
            None, 
            generate_executive_report,
            state["requirements"],
            state["resources"],
            state["timeline"],
            state["costs"],
            state["risks"]
        )
        state["executive_report"] = rep_result
        
        yield sse_event("Executive Report Agent", "completed", 100, "Cohesive executive report generated.", rep_result)
        await asyncio.sleep(0.5)

        # Yield the final compiled project payload
        final_payload = {
            "project_overview": rep_result.get("project_overview", {}),
            "executive_summary": rep_result.get("executive_summary", ""),
            "technology_summary": rep_result.get("technology_summary", {}),
            "resource_plan": rep_result.get("resource_plan", {}),
            "timeline": rep_result.get("timeline", {}),
            "budget": rep_result.get("budget", {}),
            "risks": rep_result.get("risks", []),
            "recommendations": rep_result.get("recommendations", []),
            "overall_readiness_score": rep_result.get("overall_readiness_score", 0),
            "processed_at": "Just now"
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
