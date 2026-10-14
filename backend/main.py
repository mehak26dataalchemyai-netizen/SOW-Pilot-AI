import os
import json
import uuid
import shutil
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pypdf import PdfReader
import io
from pydantic import BaseModel

from data import add_project, get_latest_project, get_dashboard_stats, get_all_projects
from orchestrator import run_visual_orchestrator
from agents import extract_requirements, allocate_resources, plan_timeline, estimate_costs, analyze_risks, generate_internal_bid_analysis, generate_client_proposal, generate_architecture_proposal, match_worker_to_task, compute_simulation_status

app = FastAPI(title="SOWPilot AI Backend", version="1.0.0")

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_files")
os.makedirs(TEMP_DIR, exist_ok=True)

def parse_pdf_bytes(pdf_bytes: bytes) -> str:
    """Helper to parse raw PDF bytes to text using PyPDF."""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""

def get_default_sow_text() -> str:
    """Fallback high-quality SOW text to feed to LLM when PDF reading yields nothing."""
    return """
    STATEMENT OF WORK (SOW)
    Project Name: SOWPilot Core Platform Implementation
    Client: Apex Enterprise Corp
    Duration: 16 Weeks (4 Months)
    Target Budget: $240,000
    
    1. PROJECT OVERVIEW
    Apex Enterprise Corp requires a robust project planning platform using advanced AI agents. 
    The goal is to automatically ingest SOW documents, model requirements, planning, and costs, 
    and present a delivery roadmap with high-fidelity visuals.
    
    2. TECHNICAL STACK REQUIREMENTS
    - Frontend: React 18, Vite, Tailwind CSS v3, Recharts, Framer Motion
    - Backend: Python 3.11, FastAPI, Uvicorn
    - AI Orchestration: LangGraph, Google Gemini 2.5 Flash LLM
    - Database: Local File Storage / JSON
    
    3. CORE DELIVERABLES
    - Interactive SaaS Dashboard displaying active projects, costs, and resources.
    - AI Processing Panel featuring live streaming agent node graph executions.
    - Project Details Page incorporating budget cost pie charts, timeline phases, and risk matrices.
    - Single-click deployment scripts (run_backend.bat, run_frontend.bat).
    
    4. SYSTEM CONSTRAINTS
    - Must be deployed on AWS ECS using Fargate inside a private VPC.
    - Must pass strict SOC 2 compliance constraints.
    - The PDF file processing must work end-to-end.
    
    5. TARGET MILESTONES
    - Week 2: Architectural and UI wireframe designs approved.
    - Week 6: FastAPI endpoints and LangGraph core orchestrator running in test.
    - Week 10: Complete React SPA dashboard coupled with live SSE streaming states.
    - Week 14: Automated staging deployments and QA test suite verification.
    - Week 16: System handover to Apex Enterprise IT operations.
    """

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Saves the uploaded SOW PDF temporarily and returns a file ID.
    Used to bridge standard form uploads with Server-Sent Events (SSE).
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    file_id = f"{uuid.uuid4()}_{file.filename}"
    temp_path = os.path.join(TEMP_DIR, file_id)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"file_id": file_id, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

@app.get("/process-project-stream")
async def process_project_stream(
    file_id: Optional[str] = Query(None),
    email_body: Optional[str] = Query(None),
    sender: Optional[str] = Query(None),
    subject: Optional[str] = Query(None)
):
    """
    Server-Sent Events (SSE) endpoint. Evaluates the SOW input (PDF file or raw email text),
    starts the LangGraph orchestrator, and streams state progress.
    Saves the final report to storage upon completion.
    """
    pdf_text = ""

    # 1. Read file and extract text if file_id is provided
    if file_id and file_id != "none" and file_id.strip() != "":
        temp_path = os.path.join(TEMP_DIR, file_id)
        if os.path.exists(temp_path):
            try:
                with open(temp_path, "rb") as f:
                    pdf_bytes = f.read()
                pdf_text = parse_pdf_bytes(pdf_bytes)
                if not pdf_text:
                    print("Extracted PDF text is empty.")
            except Exception as e:
                print(f"Error reading file {temp_path}: {e}")
            finally:
                # Clean up temp file
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    # 2. If no file text was retrieved, check if email_body was supplied directly
    if not pdf_text and email_body and email_body.strip() != "":
        pdf_text = email_body

    # 3. Fallback to default SOW template if both are empty
    if not pdf_text:
        print("No SOW input detected (no file or body). Using default mock SOW text.")
        pdf_text = get_default_sow_text()

    # 2. Define custom SSE generator
    async def sse_generator():
        final_result = None
        # Stream orchestrator progress
        async for event_line in run_visual_orchestrator(pdf_text):
            yield event_line
            # Capture the final result from the stream payload to write to data.py
            if event_line.startswith("data:"):
                try:
                    payload = event_line[5:].strip()
                    parsed = json.loads(payload)
                    if parsed.get("type") == "final_result":
                        final_result = parsed.get("data")
                except Exception:
                    pass

        # Save to database if successful
        if final_result:
            # Overwrite processing meta with incoming email properties if available
            final_result["email_metadata"] = {
                "sender": sender or "apex-delivery@gmail.com",
                "subject": subject or "Apex SOW Proposal",
                "attachment_name": file_id.split("_", 1)[-1] if file_id else "direct_input",
                "message_id": None
            }
            # Append project record — run off the event loop since add_project() does blocking
            # ChromaDB indexing and compliance evaluation (never block the SSE stream's event loop).
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, add_project, final_result, pdf_text)

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

@app.post("/process-project")
async def process_project(
    sender: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    email_body: Optional[str] = Form(None),
    attachment_name: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Synchronous project processing route. Used for direct server integrations 
    and webhooks (e.g. standard Gmail trigger). Can ingest single/multiple SOW PDFs
    or raw email body text, returning the final processed result(s).
    """
    try:
        inputs_to_process = []

        # 1. Collect from files
        all_files = []
        if file:
            all_files.append(file)
        if files:
            all_files.extend(files)

        for f in all_files:
            pdf_bytes = await f.read()
            pdf_text = parse_pdf_bytes(pdf_bytes)
            if pdf_text:
                inputs_to_process.append({
                    "text": pdf_text,
                    "source_name": f.filename
                })
            else:
                print(f"File {f.filename} was parsed but yielded no text.")

        # 2. Collect from email body text (if provided, or if no files were successfully parsed)
        if email_body and email_body.strip():
            inputs_to_process.append({
                "text": email_body,
                "source_name": "Email Body Text"
            })

        # 3. Fallback to default if everything is empty
        if not inputs_to_process:
            print("No valid file or body text provided. Running with default SOW text.")
            inputs_to_process.append({
                "text": get_default_sow_text(),
                "source_name": "Default SOW template"
            })

        results = []
        loop = asyncio.get_running_loop()

        for item in inputs_to_process:
            text = item["text"]
            source_name = item["source_name"]

            # Run LangGraph nodes synchronously
            reqs = await loop.run_in_executor(None, extract_requirements, text)

            if reqs.get("project_name"):
                from database import save_requirement_version
                await loop.run_in_executor(None, save_requirement_version, reqs["project_name"], 1, reqs)

            async def run_res(): return await loop.run_in_executor(None, allocate_resources, reqs)
            async def run_risk(): return await loop.run_in_executor(None, analyze_risks, reqs)
            async def run_arch(): return await loop.run_in_executor(None, generate_architecture_proposal, reqs)

            res_task = asyncio.create_task(run_res())
            risk_task = asyncio.create_task(run_risk())
            arch_task = asyncio.create_task(run_arch())

            res, risk, arch = await asyncio.gather(res_task, risk_task, arch_task)

            # Timeline needs the actual assigned team from resources above
            time = await loop.run_in_executor(None, plan_timeline, reqs, res)

            # Cost's contingency buffer is risk-driven, so estimate it last
            cost = await loop.run_in_executor(None, estimate_costs, reqs, res, time, risk)

            report = await loop.run_in_executor(None, generate_internal_bid_analysis, reqs, res, time, cost, risk)
            proposal = await loop.run_in_executor(None, generate_client_proposal, reqs, res, time, cost, risk)

            sim_status = compute_simulation_status(reqs, res, time, cost, risk, report, proposal, arch)

            final_payload = {
                "project_overview": report.get("project_overview", {}),
                "executive_summary": report.get("executive_summary", ""),
                "technology_summary": report.get("technology_summary", {}),
                "resource_plan": report.get("resource_plan", {}),
                "timeline": report.get("timeline", {}),
                "budget": report.get("budget", {}),
                "architecture_proposal": arch,
                "client_proposal": proposal,
                "bid_details": {
                    "submission_deadline": reqs.get("submission_deadline"),
                    "pre_bid_question_deadline": reqs.get("pre_bid_question_deadline"),
                    "required_certifications": reqs.get("required_certifications", []),
                    "required_bid_documents": reqs.get("required_bid_documents", []),
                    "evaluation_criteria": reqs.get("evaluation_criteria", [])
                },
                "risks": report.get("risks", []),
                "recommendations": report.get("recommendations", []),
                "overall_readiness_score": report.get("overall_readiness_score", 0),
                "processed_at": datetime.now().strftime("%b %d, %Y %I:%M %p"),
                "is_simulated": sim_status["is_simulated"],
                "simulation_notice": sim_status["simulation_notice"],
                "email_metadata": {
                    "sender": sender or "apex-delivery@gmail.com",
                    "subject": subject or "Apex SOW Ingestion",
                    "attachment_name": attachment_name or source_name,
                    "message_id": None
                }
            }

            # add_project() does ChromaDB vector-store indexing and compliance evaluation
            # synchronously — run it off the event loop so it can't block concurrent requests
            # (same class of bug fixed for /match-workers earlier: never do blocking work inline
            # inside an async def route handler).
            await loop.run_in_executor(None, add_project, final_payload, text)
            results.append(final_payload)

        # Return single report directly, or list if multiple were processed
        if len(results) == 1:
            return results[0]
        return {"processed_projects": results}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Orchestration failure: {str(e)}")

@app.get("/project")
async def get_project():
    """Retrieve the latest processed project SOW analysis."""
    p = get_latest_project()
    if not p:
        return JSONResponse(status_code=404, content={"detail": "No projects have been processed yet."})
    return p

@app.get("/projects")
async def get_projects():
    """Retrieve all projects with their full details."""
    from data import migrate_empty_budgets, deduplicate_projects, backfill_missing_requirement_versions
    # Trigger background deduplication and repair tasks to self-heal the database
    def self_heal_db():
        deduplicate_projects()
        migrate_empty_budgets()
        backfill_missing_requirement_versions()
    asyncio.create_task(asyncio.to_thread(self_heal_db))
    return get_all_projects()

@app.get("/dashboard")
async def get_dashboard():
    """Retrieve historical dashboard metrics."""
    return get_dashboard_stats()

class ApproveBudgetRequest(BaseModel):
    project_name: str
    approved: bool

class SendProposalRequest(BaseModel):
    to_email: str
    project_name: str
    client_name: str
    budget_data: Dict[str, Any]
    timeline_weeks: str

@app.post("/project/approve")
async def approve_project(req: ApproveBudgetRequest):
    from data import update_project_approval
    success = update_project_approval(req.project_name, req.approved)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "success", "message": f"Project budget approval updated to {req.approved}"}

@app.post("/project/send-proposal")
async def send_proposal(req: SendProposalRequest):
    from gmail_service import send_proposal_email
    # send_proposal_email() makes a blocking SMTP connection — run off the event loop so a slow
    # mail server can't freeze concurrent requests (same class of bug as the IMAP polling loop).
    loop = asyncio.get_running_loop()
    success, msg = await loop.run_in_executor(
        None, send_proposal_email, req.to_email, req.project_name, req.client_name, req.budget_data, req.timeline_weeks
    )
    if not success:
        raise HTTPException(status_code=500, detail=msg)
    return {"status": "success", "message": msg}

@app.get("/test-bedrock")
async def test_bedrock():
    import traceback
    try:
        from agents import call_bedrock_json, is_api_key_valid
        if not is_api_key_valid():
            return {"status": "error", "message": "AWS Bedrock credentials not set in environment."}
        result = call_bedrock_json("Respond with a JSON object: {\"message\": \"hello\"}", "Respond with ONLY valid JSON.")
        return {"status": "success", "response": result}
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "message": str(e),
            "traceback": traceback.format_exc()
        }

@app.post("/scan-gmail")
async def scan_gmail():
    """Manual endpoint to force scanning the configured Gmail inbox immediately."""
    from gmail_service import scan_and_process_gmail_inbox
    res = await scan_and_process_gmail_inbox()
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return res

async def gmail_polling_loop():
    """Background polling loop that checks Gmail for new unread SOW emails every 30 seconds."""
    print("[GMAIL] Automated background polling loop started.")
    await asyncio.sleep(5)  # Wait 5 seconds after startup before scanning first time
    from gmail_service import scan_and_process_gmail_inbox
    while True:
        try:
            res = await scan_and_process_gmail_inbox()
            if res.get("status") == "success" and res.get("processed_sows", 0) > 0:
                print(f"[GMAIL] Automated scan processed {res['processed_sows']} new SOW project(s) from emails.")
        except Exception as e:
            print(f"[GMAIL] Error in background email polling loop: {e}")
        await asyncio.sleep(30)

class MatchWorkersRequest(BaseModel):
    task: str
    workers: List[Dict[str, Any]]

def _retrieve_and_rerank_workers(task: str, workers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Runs the blocking retrieval (vector indexing + query) and LLM rerank off the event loop."""
    from retriever import PersistentVectorStore

    # 1. Initialize persistent vector store database
    store = PersistentVectorStore()

    # 2. Add/Index all active worker profiles into the candidate_resumes collection.
    # ChromaDB metadata values must be scalars, not lists — JSON-encode list fields
    # (skills, assignments) so a real upsert doesn't fail and silently fall back every call.
    for w in workers:
        w_id = w.get("id")
        skills_str = ", ".join(w.get("skills", []))
        resume_text = f"Name: {w.get('name')}. Role: {w.get('role')}. Skills: {skills_str}."
        metadata = {**w, "skills": json.dumps(w.get("skills", [])), "assignments": json.dumps(w.get("assignments", []))}
        store.add_document("candidate_resumes", w_id, resume_text, metadata)

    # 3. Query the RAG database collection for the top candidates (Retrieval Phase)
    matched_candidates = store.query("candidate_resumes", task, top_k=5)

    # Extract full worker dictionaries to send to the LLM, decoding the JSON-encoded fields back
    def _decode_list_field(value):
        # Metadata may come back already as a list (custom JSON-store fallback path,
        # or stale cache entries from before this field was JSON-encoded) or as the
        # JSON-encoded string we write for real ChromaDB. Handle both.
        if isinstance(value, list):
            return value
        if isinstance(value, str) and value:
            try:
                return json.loads(value)
            except (ValueError, TypeError):
                return []
        return []

    if matched_candidates:
        filtered_workers = []
        for m in matched_candidates:
            meta = dict(m["metadata"])
            meta["skills"] = _decode_list_field(meta.get("skills"))
            meta["assignments"] = _decode_list_field(meta.get("assignments"))
            filtered_workers.append(meta)
    else:
        filtered_workers = workers

    # 4. Rerank the top candidates using LLM reasoning (Generation / Reranking Phase)
    return match_worker_to_task(task, filtered_workers)

@app.post("/match-workers")
async def api_match_workers(payload: MatchWorkersRequest):
    """Semantic candidate matching endpoint."""
    loop = asyncio.get_running_loop()
    try:
        res = await loop.run_in_executor(None, _retrieve_and_rerank_workers, payload.task, payload.workers)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/project/{project_name}/policies")
async def get_project_policies(project_name: str):
    from database import get_policy_checks
    import urllib.parse
    decoded_name = urllib.parse.unquote(project_name)
    res = get_policy_checks(decoded_name)
    if not res:
        res = get_policy_checks(project_name)
    return res

@app.get("/project/{project_name}/audit")
async def get_project_audit(project_name: str):
    from database import get_audit_logs
    import urllib.parse
    decoded_name = urllib.parse.unquote(project_name)
    res = get_audit_logs(decoded_name)
    if not res:
        res = get_audit_logs(project_name)
    return res

@app.get("/project/{project_name}/evaluations")
async def get_project_evaluations(project_name: str):
    from database import get_evaluations
    import urllib.parse
    decoded_name = urllib.parse.unquote(project_name)
    res = get_evaluations(decoded_name)
    if not res:
        res = get_evaluations(project_name)
    return res

@app.get("/workers")
async def api_get_workers():
    from database import get_db_workers
    return get_db_workers()

@app.post("/workers")
async def api_add_worker(worker: Dict[str, Any]):
    from database import add_db_worker
    try:
        add_db_worker(worker)
        return {"status": "success", "message": "Worker added to SQL database"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/workers/{w_id}")
async def api_delete_worker(w_id: str):
    from database import delete_db_worker
    try:
        delete_db_worker(w_id)
        return {"status": "success", "message": "Worker removed from SQL database"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AssignWorkerRequest(BaseModel):
    project_name: str
    task: str
    worker_id: str

@app.post("/assign-worker")
async def api_assign_worker(payload: AssignWorkerRequest):
    """Persists a worker-to-project assignment decided from the RAG/LLM match results."""
    from database import get_db_workers, update_worker_status
    workers = get_db_workers()
    worker = next((w for w in workers if w.get("id") == payload.worker_id), None)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    assignments = worker.get("assignments", [])
    assignments.append({"projectName": payload.project_name, "task": payload.task})
    try:
        update_worker_status(payload.worker_id, "Assigned", assignments)
        return {"status": "success", "worker_id": payload.worker_id, "assignments": assignments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/qualify-bid/{project_name}")
async def api_qualify_bid(project_name: str):
    """Runs (or re-runs) the deterministic Go/No-Go bid qualification check for a project,
    using its stored requirements (deadlines, mandatory certifications) against the org's
    actual capability list. Persists the recommendation and resets any prior human decision.
    Any missing certification also auto-seeds a pre-bid question asking the client whether an
    equivalent is acceptable — per stakeholder feedback, a cert gap shouldn't be a dead end,
    it should be a question back to the client first."""
    from data import get_project_by_name
    from database import (
        get_org_capabilities, save_bid_qualification, get_bid_qualification,
        get_pre_bid_questions, add_pre_bid_question
    )
    from agents import qualify_bid

    project = get_project_by_name(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    bid_details = project.get("bid_details", {})
    requirements = {
        "submission_deadline": bid_details.get("submission_deadline"),
        "pre_bid_question_deadline": bid_details.get("pre_bid_question_deadline"),
        "required_certifications": bid_details.get("required_certifications", [])
    }

    org_caps = get_org_capabilities()
    loop = asyncio.get_running_loop()
    qual = await loop.run_in_executor(None, qualify_bid, requirements, org_caps)
    await loop.run_in_executor(None, save_bid_qualification, project_name, qual)

    missing_certs = qual.get("missing_certifications", [])
    if missing_certs:
        existing_questions = {q["question"] for q in get_pre_bid_questions(project_name)}
        our_caps_str = ", ".join(org_caps) if org_caps else "our current certifications"
        for cert in missing_certs:
            question = (
                f"Our organization does not currently hold '{cert}'. Would you accept {our_caps_str} "
                f"as an equivalent, or grant an exemption for this requirement?"
            )
            if question not in existing_questions:
                await loop.run_in_executor(None, add_pre_bid_question, project_name, question)

    return get_bid_qualification(project_name)

@app.get("/qualify-bid/{project_name}")
async def api_get_bid_qualification(project_name: str):
    from database import get_bid_qualification
    record = get_bid_qualification(project_name)
    if not record:
        raise HTTPException(status_code=404, detail="No qualification record for this project yet")
    return record

class BidDecisionRequest(BaseModel):
    decision: str  # 'Go' | 'No-Go'
    decided_by: str = "Delivery Owner"

@app.post("/qualify-bid/{project_name}/decision")
async def api_set_bid_decision(project_name: str, payload: BidDecisionRequest):
    from database import get_bid_qualification, set_bid_decision
    if payload.decision not in ("Go", "No-Go"):
        raise HTTPException(status_code=400, detail="decision must be 'Go' or 'No-Go'")
    if not get_bid_qualification(project_name):
        raise HTTPException(status_code=404, detail="No qualification record for this project yet")
    set_bid_decision(project_name, payload.decision, payload.decided_by)
    return get_bid_qualification(project_name)

class AssignDeliveryOwnerRequest(BaseModel):
    owner_name: str

@app.post("/qualify-bid/{project_name}/assign-owner")
async def api_assign_delivery_owner(project_name: str, payload: AssignDeliveryOwnerRequest):
    """Assigns the delivery owner as soon as a bid is qualified — not just at final sign-off —
    so the person who will actually deliver the project if won is engaged from day one and can
    track solutioning/pricing as it develops, per stakeholder feedback."""
    from database import get_bid_qualification, assign_delivery_owner
    if not get_bid_qualification(project_name):
        raise HTTPException(status_code=404, detail="No qualification record for this project yet — run qualification first")
    assign_delivery_owner(project_name, payload.owner_name)
    return get_bid_qualification(project_name)

@app.get("/org-capabilities")
async def api_get_org_capabilities():
    from database import get_org_capabilities
    return get_org_capabilities()

class OrgCapabilityRequest(BaseModel):
    certification: str

@app.post("/org-capabilities")
async def api_add_org_capability(payload: OrgCapabilityRequest):
    from database import add_org_capability, get_org_capabilities
    add_org_capability(payload.certification)
    return get_org_capabilities()

@app.delete("/org-capabilities/{certification}")
async def api_remove_org_capability(certification: str):
    from database import remove_org_capability, get_org_capabilities
    remove_org_capability(certification)
    return get_org_capabilities()

@app.get("/org-settings/default-margin")
async def api_get_default_margin():
    from database import get_org_setting
    return {"default_margin_percent": float(get_org_setting("default_margin_percent", "15"))}

class MarginSettingRequest(BaseModel):
    margin_percent: float

@app.post("/org-settings/default-margin")
async def api_set_default_margin(payload: MarginSettingRequest):
    from database import set_org_setting
    if payload.margin_percent < 0 or payload.margin_percent > 100:
        raise HTTPException(status_code=400, detail="margin_percent must be between 0 and 100")
    set_org_setting("default_margin_percent", str(payload.margin_percent))
    return {"default_margin_percent": payload.margin_percent}

@app.post("/pre-bid-questions/{project_name}/generate")
async def api_generate_pre_bid_questions(project_name: str):
    """Drafts (or re-drafts) clarifying questions from requirements_v1. Re-running clears any
    still-pending (unanswered) questions first, so repeated clicks don't pile up duplicates —
    already-answered questions are preserved as a permanent record."""
    from database import get_requirement_version, clear_pending_pre_bid_questions, add_pre_bid_question, get_pre_bid_questions
    from agents import generate_clarifying_questions

    reqs_v1 = get_requirement_version(project_name, 1)
    if not reqs_v1:
        raise HTTPException(status_code=404, detail="No requirements_v1 snapshot found for this project")

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, generate_clarifying_questions, reqs_v1)
    questions = result.get("questions", [])

    await loop.run_in_executor(None, clear_pending_pre_bid_questions, project_name)
    for q in questions:
        await loop.run_in_executor(None, add_pre_bid_question, project_name, q)

    return get_pre_bid_questions(project_name)

@app.get("/pre-bid-questions/{project_name}")
async def api_get_pre_bid_questions(project_name: str):
    from database import get_pre_bid_questions
    return get_pre_bid_questions(project_name)

class AnswerQuestionRequest(BaseModel):
    client_answer: str

@app.post("/pre-bid-questions/{project_name}/{question_id}/answer")
async def api_answer_pre_bid_question(project_name: str, question_id: int, payload: AnswerQuestionRequest):
    from database import answer_pre_bid_question, get_pre_bid_questions
    if not answer_pre_bid_question(question_id, payload.client_answer):
        raise HTTPException(status_code=404, detail="Question not found")
    return get_pre_bid_questions(project_name)

async def _finalize_and_requalify(project_name: str, extra_exemptions: List[str] = None) -> Optional[Dict[str, Any]]:
    """Shared by the manual 'Re-finalize v2' action and the automated 'Fetch Answers from Mail' flow,
    so BOTH paths give the same benefit: merging the full answered set into requirements_v2, scanning
    ALL of it (not just newly-arrived answers) for any certification exemption the client has granted,
    and re-running the Go/No-Go qualification check against the updated picture. Returns None if there's
    no v1 snapshot to build from (nothing to finalize)."""
    from database import (
        get_requirement_version, get_pre_bid_questions, save_requirement_version,
        get_org_capabilities, save_bid_qualification, get_bid_qualification
    )
    from agents import merge_requirements_with_answers, detect_certification_exemptions, qualify_bid

    reqs_v1 = get_requirement_version(project_name, 1)
    if not reqs_v1:
        return None

    questions = get_pre_bid_questions(project_name)
    answered = [q for q in questions if q.get("status") == "Answered"]
    qa_pairs = [{"question": q["question"], "answer": q["client_answer"]} for q in answered]

    loop = asyncio.get_running_loop()
    detected_exemptions = await loop.run_in_executor(None, detect_certification_exemptions, qa_pairs) if qa_pairs else []

    prior_v2 = get_requirement_version(project_name, 2) or {}
    accumulated_exemptions = list(set(
        (prior_v2.get("exempted_certifications") or []) + detected_exemptions + (extra_exemptions or [])
    ))

    reqs_v2 = merge_requirements_with_answers(reqs_v1, qa_pairs, accumulated_exemptions)
    save_requirement_version(project_name, 2, reqs_v2)

    org_caps = get_org_capabilities()
    qual_requirements = {
        "submission_deadline": reqs_v2.get("submission_deadline"),
        "pre_bid_question_deadline": reqs_v2.get("pre_bid_question_deadline"),
        "required_certifications": reqs_v2.get("required_certifications", [])
    }
    new_qual = await loop.run_in_executor(None, qualify_bid, qual_requirements, org_caps, accumulated_exemptions)
    save_bid_qualification(project_name, new_qual)

    return {"requirements_v2": reqs_v2, "qualification": get_bid_qualification(project_name)}

@app.post("/pre-bid-questions/{project_name}/finalize")
async def api_finalize_pre_bid_questions(project_name: str):
    """Merges all answered pre-bid questions into requirements_v2, layered on top of the untouched
    v1 snapshot (v1 remains available and unmodified for audit purposes), and re-runs the Go/No-Go
    qualification check against the updated picture — so answering questions manually gets the same
    benefit as fetching answers from a client's email reply."""
    result = await _finalize_and_requalify(project_name)
    if result is None:
        raise HTTPException(status_code=404, detail="No requirements_v1 snapshot found for this project")
    return result

@app.get("/pre-bid-questions/{project_name}/draft-email")
async def api_draft_pre_bid_email(project_name: str):
    """Compiles all still-pending (unanswered) pre-bid questions into a reviewable client email draft.
    Also resolves the recipient address and whether this project was actually ingested from a Gmail
    thread (so the frontend knows whether Send will reply in-thread or go out as a fresh email)."""
    from database import get_pre_bid_questions
    from data import get_project_by_name
    from gmail_service import compose_pre_bid_email_draft, extract_email_address

    questions = get_pre_bid_questions(project_name)
    pending = [q["question"] for q in questions if q.get("status") == "Pending"]
    if not pending:
        raise HTTPException(status_code=400, detail="No pending pre-bid questions to draft an email for.")

    project = get_project_by_name(project_name)
    email_meta = (project or {}).get("email_metadata") or {}
    client = (project or {}).get("project_overview", {}).get("client", "")
    to_email = extract_email_address(email_meta.get("sender", ""))

    draft = compose_pre_bid_email_draft(project_name, client, pending)
    return {
        "to_email": to_email,
        "subject": draft["subject"],
        "body": draft["body"],
        "is_threaded_reply": bool(email_meta.get("message_id")),
        "original_subject": email_meta.get("subject")
    }

class SendPreBidEmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str

@app.post("/pre-bid-questions/{project_name}/send-email")
async def api_send_pre_bid_email(project_name: str, payload: SendPreBidEmailRequest):
    """Sends the (possibly user-edited) draft to the client. If the project was ingested from a Gmail
    thread, sends as a reply in that same thread (In-Reply-To/References + 'Re:' subject); otherwise
    sends as a standalone email to the address the user supplied/edited. Records the Message-ID we set
    on this send so a later 'fetch answers from mail' call knows which thread to search for a reply in."""
    from data import get_project_by_name, set_outbound_message_id
    from gmail_service import send_reply_in_thread

    if not payload.to_email or "@" not in payload.to_email:
        raise HTTPException(status_code=400, detail="A valid recipient email address is required.")

    project = get_project_by_name(project_name)
    email_meta = (project or {}).get("email_metadata") or {}
    in_reply_to = email_meta.get("message_id")

    loop = asyncio.get_running_loop()
    success, msg, our_message_id = await loop.run_in_executor(
        None, send_reply_in_thread, payload.to_email, payload.subject, payload.body, in_reply_to
    )
    if not success:
        raise HTTPException(status_code=500, detail=msg)

    if our_message_id:
        await loop.run_in_executor(None, set_outbound_message_id, project_name, our_message_id)

    return {"status": "success", "message": msg, "sent_in_thread": bool(in_reply_to)}

@app.get("/project/{project_name}/proposal-email/draft")
async def api_draft_proposal_email(project_name: str):
    """Compiles the generated client_proposal (the actual persuasive bid response, separate from the
    internal analysis) into a reviewable email draft — this is the document the whole pipeline exists
    to produce, so it needs its own send action distinct from the older budget-only proposal email."""
    from data import get_project_by_name
    from gmail_service import compose_client_proposal_email, extract_email_address

    project = get_project_by_name(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    client_proposal = project.get("client_proposal")
    if not client_proposal:
        raise HTTPException(status_code=400, detail="No client proposal has been generated for this project yet.")

    email_meta = project.get("email_metadata") or {}
    client = project.get("project_overview", {}).get("client", "")
    to_email = extract_email_address(email_meta.get("sender", ""))

    draft = compose_client_proposal_email(client_proposal, project_name, client)
    return {
        "to_email": to_email,
        "subject": draft["subject"],
        "body": draft["body"],
        "is_threaded_reply": bool(email_meta.get("message_id")),
        "original_subject": email_meta.get("subject"),
        "pdf_attached": True
    }

@app.get("/project/{project_name}/proposal-email/pdf-preview")
async def api_preview_proposal_pdf(project_name: str):
    """Streams the formatted proposal PDF so it can be previewed/downloaded before sending — the exact
    file that will be attached to the outbound email, built fresh from the project's current data."""
    from fastapi.responses import Response
    from data import get_project_by_name
    from proposal_pdf import generate_proposal_pdf

    project = get_project_by_name(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    client_proposal = project.get("client_proposal")
    if not client_proposal:
        raise HTTPException(status_code=400, detail="No client proposal has been generated for this project yet.")

    client = project.get("project_overview", {}).get("client", "")
    loop = asyncio.get_running_loop()
    pdf_bytes = await loop.run_in_executor(
        None, generate_proposal_pdf, client_proposal, project_name, client,
        project.get("budget"), project.get("timeline"), project.get("resource_plan")
    )
    filename = f"Proposal_{project_name.replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )

class SendProposalEmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str
    client_feedback: str = ""  # what prompted this round, e.g. the client's counter/questions from a prior send

@app.post("/project/{project_name}/proposal-email/send")
async def api_send_proposal_email_doc(project_name: str, payload: SendProposalEmailRequest):
    """Sends the (possibly user-edited) client proposal draft, with the formatted proposal PDF attached
    (built fresh server-side from the project's current data, not trusted from the client). Threads as a
    reply to the original inbound SOW email when this project was ingested from Gmail; otherwise sends
    standalone. Each successful send is logged as a new version in proposal_revisions — this is a
    revise-and-resend TRACKING layer, not an automated negotiation engine; a human still edits the
    subject/body for each round."""
    from data import get_project_by_name
    from gmail_service import send_reply_in_thread
    from proposal_pdf import generate_proposal_pdf

    if not payload.to_email or "@" not in payload.to_email:
        raise HTTPException(status_code=400, detail="A valid recipient email address is required.")

    project = get_project_by_name(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    client_proposal = project.get("client_proposal")
    if not client_proposal:
        raise HTTPException(status_code=400, detail="No client proposal has been generated for this project yet.")

    email_meta = project.get("email_metadata") or {}
    in_reply_to = email_meta.get("message_id")
    client = project.get("project_overview", {}).get("client", "")

    loop = asyncio.get_running_loop()
    pdf_bytes = await loop.run_in_executor(
        None, generate_proposal_pdf, client_proposal, project_name, client,
        project.get("budget"), project.get("timeline"), project.get("resource_plan")
    )
    pdf_filename = f"Proposal_{project_name.replace(' ', '_')}.pdf"

    success, msg, our_message_id = await loop.run_in_executor(
        None, send_reply_in_thread, payload.to_email, payload.subject, payload.body, in_reply_to,
        pdf_bytes, pdf_filename
    )
    if not success:
        raise HTTPException(status_code=500, detail=msg)

    from database import add_proposal_revision
    from data import set_outbound_message_id
    if our_message_id:
        await loop.run_in_executor(None, set_outbound_message_id, project_name, our_message_id, "proposal_outbound_message_id")
    revisions = await loop.run_in_executor(
        None, add_proposal_revision, project_name, payload.subject, payload.body,
        bool(in_reply_to), payload.client_feedback, our_message_id
    )
    return {
        "status": "success", "message": msg, "sent_in_thread": bool(in_reply_to),
        "pdf_attached": True, "version": revisions[-1]["version"] if revisions else 1
    }

@app.get("/proposal-revisions/{project_name}")
async def api_get_proposal_revisions(project_name: str):
    from database import get_proposal_revisions
    return get_proposal_revisions(project_name)

@app.post("/project/{project_name}/proposal-email/fetch-response")
async def api_fetch_proposal_response(project_name: str):
    """Checks the client's email thread for a reply to the proposal we sent, and classifies it as
    Accepted / Rejected / Revision Requested using an LLM reading of the actual reply text. Searches
    across EVERY version's Message-ID (not just the most recent send) — a client may reply to an
    earlier version of the proposal, not necessarily the latest resend. Returns the classification
    only — it never writes to Win/Loss or starts a new revision automatically; a human confirms that
    action from the UI. Returns found=False if no reply has arrived yet."""
    from data import get_project_by_name
    from agents import classify_proposal_response
    from gmail_service import fetch_thread_reply
    from database import get_proposal_message_ids

    project = get_project_by_name(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    loop = asyncio.get_running_loop()
    message_ids = await loop.run_in_executor(None, get_proposal_message_ids, project_name)
    if not message_ids:
        email_meta = project.get("email_metadata") or {}
        fallback_id = email_meta.get("proposal_outbound_message_id")
        message_ids = [fallback_id] if fallback_id else []
    if not message_ids:
        raise HTTPException(status_code=400, detail="No proposal email has been sent for this project yet.")

    reply_text = None
    for mid in message_ids:
        reply_text = await loop.run_in_executor(None, fetch_thread_reply, mid)
        if reply_text:
            break
    if not reply_text:
        return {"found": False, "message": "No reply found in the thread yet."}

    classification = await loop.run_in_executor(None, classify_proposal_response, reply_text)
    return {"found": True, "reply_text": reply_text, **classification}

class ChangeDecision(BaseModel):
    change: str
    decision: str  # 'Accept' | 'Decline' | 'Partial'
    note: str = ""
    price_adjustment_percent: Optional[float] = None  # e.g. -10 for a 10% reduction negotiated with the client

class RedraftProposalRequest(BaseModel):
    decisions: List[ChangeDecision]

@app.post("/project/{project_name}/proposal-email/draft-reply")
async def api_draft_client_reply(project_name: str, payload: RedraftProposalRequest):
    """Drafts a short, focused REPLY addressing each client-requested change, per a human's
    Accept/Decline/Partial decision on every item — NOT a full proposal re-send.

    Any decision carrying a price_adjustment_percent is applied FIRST, deterministically, via the same
    apply_price_adjustment() mechanism the Approvals tab already uses — this is the single source of
    truth for the bid price, so the adjustment instantly flows into the PDF's investment table, the
    Resources tab budget dashboard, and the Dashboard project card, not just this email's wording. The
    real resulting figure is then handed to the drafting agent to state verbatim, so the email can never
    say a different number than what the system actually recorded."""
    from data import get_project_by_name, apply_price_adjustment
    from agents import draft_client_reply
    from gmail_service import extract_email_address
    from database import get_proposal_revisions

    if not payload.decisions:
        raise HTTPException(status_code=400, detail="At least one change decision is required.")

    project = get_project_by_name(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    email_meta = project.get("email_metadata") or {}
    client = project.get("project_overview", {}).get("client", "")
    to_email = extract_email_address(email_meta.get("sender", ""))

    loop = asyncio.get_running_loop()

    decisions_payload = [d.dict() for d in payload.decisions]
    for d in decisions_payload:
        pct = d.pop("price_adjustment_percent", None)
        if d["decision"] == "Accept" and pct:
            reason = f"Client-negotiated — {d['change']}" + (f" ({d['note']})" if d.get("note") else "")
            updated_budget = await loop.run_in_executor(None, apply_price_adjustment, project_name, pct, reason)
            if updated_budget:
                new_price = updated_budget.get("bid_price")
                d["note"] = (d.get("note") or "").strip()
                d["note"] += f" — new total investment: ${new_price:,.2f}" if new_price else ""
                d["note"] = d["note"].strip(" —")

    draft = await loop.run_in_executor(None, draft_client_reply, decisions_payload, client)

    revisions = await loop.run_in_executor(None, get_proposal_revisions, project_name)
    last_subject = revisions[-1]["subject"] if revisions else f"Proposal: {project_name}"
    subject = last_subject if last_subject.lower().startswith("re:") else f"Re: {last_subject}"

    return {"to_email": to_email, "subject": subject, "body": draft["body"]}

class SendClientReplyRequest(BaseModel):
    to_email: str
    subject: str
    body: str

@app.post("/project/{project_name}/proposal-email/send-reply")
async def api_send_client_reply(project_name: str, payload: SendClientReplyRequest):
    """Sends a focused reply (no PDF attachment, no proposal re-send) threaded into the same
    conversation. Logged into the same revision history as a lightweight entry — mainly so its
    Message-ID is tracked and a later 'Fetch Client Response' can find the client's next reply."""
    from data import get_project_by_name, set_outbound_message_id
    from database import add_proposal_revision
    from gmail_service import send_reply_in_thread

    if not payload.to_email or "@" not in payload.to_email:
        raise HTTPException(status_code=400, detail="A valid recipient email address is required.")

    project = get_project_by_name(project_name)
    email_meta = (project or {}).get("email_metadata") or {}
    in_reply_to = email_meta.get("message_id")

    loop = asyncio.get_running_loop()
    success, msg, our_message_id = await loop.run_in_executor(
        None, send_reply_in_thread, payload.to_email, payload.subject, payload.body, in_reply_to
    )
    if not success:
        raise HTTPException(status_code=500, detail=msg)

    if our_message_id:
        await loop.run_in_executor(None, set_outbound_message_id, project_name, our_message_id, "proposal_outbound_message_id")
        await loop.run_in_executor(
            None, add_proposal_revision, project_name, payload.subject, payload.body,
            bool(in_reply_to), "Reply addressing client's requested changes", our_message_id
        )

    return {"status": "success", "message": msg, "sent_in_thread": bool(in_reply_to)}

@app.get("/contract-status/{project_name}")
async def api_get_contract_status(project_name: str):
    from database import get_contract_status
    record = get_contract_status(project_name)
    return record or {"project_name": project_name, "status": "Not Started", "notes": None, "updated_by": None, "updated_at": None}

class ContractStatusRequest(BaseModel):
    status: str  # 'Not Started' | 'Sent for Signature' | 'Signed' | 'Rejected'
    notes: str = ""
    updated_by: str = "Delivery Owner"

@app.post("/contract-status/{project_name}")
async def api_set_contract_status(project_name: str, payload: ContractStatusRequest):
    from database import set_contract_status
    valid_statuses = ("Not Started", "Sent for Signature", "Signed", "Rejected")
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"status must be one of {valid_statuses}")
    return set_contract_status(project_name, payload.status, payload.notes, payload.updated_by)

@app.get("/project/{project_name}/timeline/revisions")
async def api_get_timeline_revisions(project_name: str):
    from database import get_timeline_revisions
    return get_timeline_revisions(project_name)

class TimelineAdjustmentRequest(BaseModel):
    trigger_type: str  # 'Dependency Delay' | 'Scope Change' | 'Resource Conflict' | 'Velocity Variance' | 'Other'
    affected_phase: str
    delta_weeks: float
    reason: str
    applied_by: str = "Delivery Owner"

@app.post("/project/{project_name}/timeline/adjust")
async def api_adjust_timeline(project_name: str, payload: TimelineAdjustmentRequest):
    """Logs a real schedule disruption and ripples it through the plan deterministically — this is the
    real-world mechanism a delay/scope-change/resource-conflict actually goes through: the critical-path
    shift is computed exactly (never guessed), the resulting cost impact is computed by re-running the
    same deterministic cost engine against the old and new timeline, and that delta is applied through
    the same traceable financial-adjustment log used for negotiated price changes — one unified history
    of why the numbers changed, not a separate ad hoc system for schedule vs. price."""
    from data import get_project_by_name, apply_cost_delta
    from database import get_requirement_version, add_timeline_revision
    from agents import apply_timeline_adjustment, estimate_costs

    valid_triggers = ("Dependency Delay", "Scope Change", "Resource Conflict", "Velocity Variance", "Other")
    if payload.trigger_type not in valid_triggers:
        raise HTTPException(status_code=400, detail=f"trigger_type must be one of {valid_triggers}")

    project = get_project_by_name(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    reqs = get_requirement_version(project_name, 1)
    if not reqs:
        raise HTTPException(status_code=400, detail="No requirements_v1 snapshot found for this project — cannot recompute cost impact.")

    resources = project.get("resource_plan") or {}
    risks = project.get("risks") or []
    old_timeline = project.get("timeline") or {}

    loop = asyncio.get_running_loop()
    try:
        new_timeline = await loop.run_in_executor(
            None, apply_timeline_adjustment, old_timeline, payload.affected_phase, payload.delta_weeks
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    old_budget = await loop.run_in_executor(None, estimate_costs, reqs, resources, old_timeline, risks)
    new_budget = await loop.run_in_executor(None, estimate_costs, reqs, resources, new_timeline, risks)
    cost_impact = round(new_budget.get("total_cost", 0) - old_budget.get("total_cost", 0), 2)

    from data import get_db_connection
    import json as _json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, full_data FROM projects WHERE project_name = ?", (project_name,))
    row = cur.fetchone()
    if not row:
        cur.execute("SELECT id, full_data FROM projects")
        for r in cur.fetchall():
            d = _json.loads(r["full_data"])
            n = d.get("project_overview", {}).get("project_name") or d.get("project_name")
            if n == project_name:
                row = r
                break
    if row:
        data = _json.loads(row["full_data"])
        data["timeline"] = new_timeline
        cur.execute("UPDATE projects SET full_data = ? WHERE id = ?", (_json.dumps(data), row["id"]))
        conn.commit()
    conn.close()

    updated_budget = None
    if cost_impact:
        reason = f"Timeline impact — {payload.trigger_type}: {payload.reason}"
        updated_budget = await loop.run_in_executor(None, apply_cost_delta, project_name, cost_impact, reason)

    await loop.run_in_executor(
        None, add_timeline_revision, project_name, payload.trigger_type, payload.affected_phase,
        payload.delta_weeks, payload.reason, cost_impact, payload.applied_by
    )

    return {
        "status": "success",
        "timeline": new_timeline,
        "cost_impact": cost_impact,
        "budget": updated_budget,
    }

@app.post("/pre-bid-questions/{project_name}/fetch-answers")
async def api_fetch_pre_bid_answers(project_name: str):
    """Checks the client's email thread for a reply to the pre-bid questions we sent, matches its
    content back to the specific pending questions, saves any confidently-matched answers, re-finalizes
    requirements_v2, and re-runs the Go/No-Go qualification check (so a client granting a certification
    exemption, for example, can flip a No-Go to a Go automatically). Returns found=False with no changes
    if no reply has arrived yet — this is an on-demand check, not automatic polling."""
    from data import get_project_by_name
    from database import get_pre_bid_questions, answer_pre_bid_question, get_bid_qualification
    from agents import match_answers_to_questions
    from gmail_service import fetch_thread_reply

    project = get_project_by_name(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    email_meta = project.get("email_metadata") or {}
    outbound_message_id = email_meta.get("last_outbound_message_id")
    if not outbound_message_id:
        raise HTTPException(status_code=400, detail="No pre-bid email has been sent for this project yet.")

    loop = asyncio.get_running_loop()
    reply_text = await loop.run_in_executor(None, fetch_thread_reply, outbound_message_id)
    if not reply_text:
        return {"found": False, "message": "No reply found in the thread yet."}

    all_questions = get_pre_bid_questions(project_name)
    pending = [q for q in all_questions if q.get("status") == "Pending"]
    if not pending:
        return {"found": True, "reply_text": reply_text, "matched_count": 0, "message": "Reply found, but no pending questions to match it against."}

    pending_texts = [q["question"] for q in pending]
    match_result = await loop.run_in_executor(None, match_answers_to_questions, reply_text, pending_texts)
    matches = match_result.get("matches", [])
    new_exemptions = match_result.get("exempted_certifications", [])

    # Save each confidently-matched answer against its actual DB row
    question_by_text = {q["question"]: q["id"] for q in pending}
    saved = 0
    for m in matches:
        q_id = question_by_text.get(m["question"])
        if q_id:
            answer_pre_bid_question(q_id, m["answer"])
            saved += 1

    updated_questions = get_pre_bid_questions(project_name)
    result_payload = {
        "found": True,
        "reply_text": reply_text,
        "matched_count": saved,
        "unmatched_count": len(pending) - saved,
        "questions": updated_questions,
        "qualification": get_bid_qualification(project_name)
    }

    # Re-finalize v2 and re-run qualification against the FULL answered set (not just this reply's
    # matches) — same shared path the manual 'Re-finalize v2' button uses.
    finalize_result = await _finalize_and_requalify(project_name, extra_exemptions=new_exemptions)
    if finalize_result:
        result_payload["requirements_v2"] = finalize_result["requirements_v2"]
        result_payload["qualification"] = finalize_result["qualification"]

    return result_payload

@app.get("/requirements/{project_name}/versions")
async def api_get_requirement_versions(project_name: str):
    from database import get_requirement_version
    v1 = get_requirement_version(project_name, 1)
    v2 = get_requirement_version(project_name, 2)
    return {"v1": v1, "v2": v2}

@app.get("/bid-documents/{project_name}")
async def api_get_bid_documents(project_name: str):
    """Returns the tracked checklist of supporting documents required to submit this bid (reference
    letters, financials, BAA templates, etc. — distinct from certifications). Auto-seeds from the
    project's extracted required_bid_documents the first time this is called for a project."""
    from data import get_project_by_name
    from database import get_bid_documents, seed_bid_documents

    existing = get_bid_documents(project_name)
    if not existing:
        project = get_project_by_name(project_name)
        required_docs = (project or {}).get("bid_details", {}).get("required_bid_documents", [])
        if required_docs:
            seed_bid_documents(project_name, required_docs)
            existing = get_bid_documents(project_name)
    return existing

class UpdateBidDocumentRequest(BaseModel):
    status: str  # 'Pending' | 'Ready' | 'Not Applicable'
    notes: str = ""

@app.post("/bid-documents/{project_name}/{doc_id}")
async def api_update_bid_document(project_name: str, doc_id: int, payload: UpdateBidDocumentRequest):
    from database import update_bid_document_status, get_bid_documents
    if payload.status not in ("Pending", "Ready", "Not Applicable"):
        raise HTTPException(status_code=400, detail="status must be 'Pending', 'Ready', or 'Not Applicable'")
    if not update_bid_document_status(doc_id, payload.status, payload.notes):
        raise HTTPException(status_code=404, detail="Bid document not found")
    return get_bid_documents(project_name)

@app.get("/delivery-review/{project_name}")
async def api_get_delivery_reviews(project_name: str):
    from database import get_delivery_owner_reviews
    return get_delivery_owner_reviews(project_name)

class DeliveryReviewRequest(BaseModel):
    reviewed_by: str = "Delivery Owner"
    notes: str = ""

@app.post("/delivery-review/{project_name}/{stage}")
async def api_set_delivery_review(project_name: str, stage: str, payload: DeliveryReviewRequest):
    """Records that the assigned delivery owner has reviewed this project at a specific stage
    (solutioning or pricing) — so their involvement is tracked throughout the bid, not just captured
    once at the final submission-ready sign-off."""
    from database import set_delivery_owner_review, get_delivery_owner_reviews
    if stage not in ("solutioning", "pricing"):
        raise HTTPException(status_code=400, detail="stage must be 'solutioning' or 'pricing'")
    set_delivery_owner_review(project_name, stage, payload.reviewed_by, payload.notes)
    return get_delivery_owner_reviews(project_name)

@app.get("/content-library")
async def api_get_content_library():
    from database import get_content_library
    return get_content_library()

class ContentLibraryEntryRequest(BaseModel):
    label: str
    content: str

@app.post("/content-library")
async def api_add_content_library_entry(payload: ContentLibraryEntryRequest):
    from database import add_content_library_entry, get_content_library
    if not payload.label.strip() or not payload.content.strip():
        raise HTTPException(status_code=400, detail="Both label and content are required.")
    add_content_library_entry(payload.label.strip(), payload.content.strip())
    return get_content_library()

@app.delete("/content-library/{entry_id}")
async def api_delete_content_library_entry(entry_id: int):
    from database import delete_content_library_entry, get_content_library
    delete_content_library_entry(entry_id)
    return get_content_library()

# --- Post-Award Lifecycle: Win/Loss, Estimate vs Actual, Cost of Bidding ---
# Everything upstream (qualification through sign-off) covers the bid/pre-award lifecycle. These three
# capture what happens after the proposal goes out — using manually-logged data since no CRM/timesheet
# integration exists yet to supply it automatically.

@app.get("/outcomes/{project_name}")
async def api_get_project_outcomes(project_name: str):
    """Returns the full post-award picture for a project in one call: win/loss decision, estimate-vs-actual
    variance, and internal cost of bidding — plus the project's own estimate figures, so the frontend can
    compute variance without a second round trip."""
    from data import get_project_by_name
    from database import get_win_loss, get_project_actuals, get_bid_cost

    project = get_project_by_name(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    budget = project.get("budget") or {}
    timeline = project.get("timeline") or {}

    return {
        "win_loss": get_win_loss(project_name),
        "actuals": get_project_actuals(project_name),
        "bid_cost": get_bid_cost(project_name),
        "estimate": {
            "total_cost": budget.get("total_cost"),
            "estimated_completion": timeline.get("estimated_completion"),
        }
    }

class WinLossRequest(BaseModel):
    status: str  # 'Won' | 'Lost'
    reason: str = ""
    decided_by: str = "Delivery Owner"

@app.post("/win-loss/{project_name}")
async def api_set_win_loss(project_name: str, payload: WinLossRequest):
    from database import set_win_loss
    if payload.status not in ("Won", "Lost"):
        raise HTTPException(status_code=400, detail="status must be 'Won' or 'Lost'")
    return set_win_loss(project_name, payload.status, payload.reason, payload.decided_by)

class ProjectActualsRequest(BaseModel):
    actual_total_cost: float
    actual_duration_weeks: float
    notes: str = ""
    logged_by: str = "Delivery Owner"

@app.post("/project-actuals/{project_name}")
async def api_set_project_actuals(project_name: str, payload: ProjectActualsRequest):
    """Logs real delivery numbers against a project so they can be compared to the original bid estimate.
    Manually entered for now — there's no timesheet/actuals feed to pull this from automatically."""
    from database import set_project_actuals
    return set_project_actuals(
        project_name, payload.actual_total_cost, payload.actual_duration_weeks,
        payload.notes, payload.logged_by
    )

class BidCostRequest(BaseModel):
    internal_hours: float
    internal_hourly_rate: float = 150
    notes: str = ""
    logged_by: str = "Delivery Owner"

@app.post("/bid-cost/{project_name}")
async def api_set_bid_cost(project_name: str, payload: BidCostRequest):
    """Logs internal hours spent preparing this bid (BD/solutioning time), independent of whether it's
    won — manually entered, since no internal time-tracking feed exists yet."""
    from database import set_bid_cost
    return set_bid_cost(
        project_name, payload.internal_hours, payload.internal_hourly_rate,
        payload.notes, payload.logged_by
    )

@app.get("/approval-contacts")
async def api_get_approval_contacts():
    from database import get_approval_contacts
    return get_approval_contacts()

class ApprovalContactRequest(BaseModel):
    department: str
    email: str

@app.post("/approval-contacts")
async def api_set_approval_contact(payload: ApprovalContactRequest):
    from database import set_approval_contact
    if not payload.department.strip() or "@" not in payload.email:
        raise HTTPException(status_code=400, detail="A department name and a valid email are required.")
    return set_approval_contact(payload.department.strip(), payload.email.strip())

@app.delete("/approval-contacts/{department}")
async def api_delete_approval_contact(department: str):
    from database import delete_approval_contact
    return delete_approval_contact(department)

@app.post("/approvals/{project_name}/generate")
async def api_generate_approvals(project_name: str):
    """Scans requirements_v1 (and the latest bid qualification, if any) for concerns that need
    routing to a specific internal stakeholder before submission. Re-running clears any still-pending
    entries first — already-resolved approvals are preserved as a permanent record.

    Newly-flagged concerns are grouped by department and, where a notification contact is configured
    for that department (Settings tab), trigger one summary email — so a routed concern is actually
    surfaced to someone instead of only appearing silently in this tab. Departments with no configured
    contact are skipped (not an error) since not every org wires this up immediately."""
    from database import (
        get_requirement_version, get_bid_qualification, clear_pending_approvals,
        add_approval, get_approvals, get_approval_contact_email
    )
    from agents import flag_approval_concerns
    from gmail_service import send_internal_notification

    reqs_v1 = get_requirement_version(project_name, 1)
    if not reqs_v1:
        raise HTTPException(status_code=404, detail="No requirements_v1 snapshot found for this project")

    qualification = get_bid_qualification(project_name)
    loop = asyncio.get_running_loop()
    concerns = await loop.run_in_executor(None, flag_approval_concerns, reqs_v1, qualification)

    await loop.run_in_executor(None, clear_pending_approvals, project_name)
    for c in concerns:
        await loop.run_in_executor(None, add_approval, project_name, c["concern_type"], c["description"], c["routed_to"])

    # Group newly-flagged concerns by department and notify each configured contact once.
    by_department: Dict[str, List[Dict[str, str]]] = {}
    for c in concerns:
        by_department.setdefault(c["routed_to"], []).append(c)

    for department, dept_concerns in by_department.items():
        contact_email = await loop.run_in_executor(None, get_approval_contact_email, department)
        if not contact_email:
            continue
        body_lines = [
            f"{len(dept_concerns)} item(s) on project \"{project_name}\" have been routed to {department} for review:",
            "",
        ]
        for c in dept_concerns:
            body_lines.append(f"- [{c['concern_type']}] {c['description']}")
        body_lines.append("")
        body_lines.append("Review and resolve in SOW Pilot under the project's Approvals tab.")
        await loop.run_in_executor(
            None, send_internal_notification, contact_email,
            f"Approval needed: {project_name} — {department}", "\n".join(body_lines)
        )

    return get_approvals(project_name)

@app.get("/approvals/{project_name}")
async def api_get_approvals(project_name: str):
    from database import get_approvals
    return get_approvals(project_name)

class ResolveApprovalRequest(BaseModel):
    status: str  # 'Approved' | 'Rejected'
    resolved_by: str = "Reviewer"
    resolution_notes: str = ""
    price_adjustment_percent: Optional[float] = None  # e.g. Finance: "+3% for Net-90 cost-of-money"

@app.post("/approvals/{project_name}/{approval_id}/resolve")
async def api_resolve_approval(project_name: str, approval_id: int, payload: ResolveApprovalRequest):
    """Resolving an approval can also move the price — a stakeholder's real answer is often
    'approved, but add X%' (e.g. Finance covering the cost of Net-90 payment terms), not a bare
    approve/reject. When price_adjustment_percent is set, it's applied to the stored bid price
    immediately, with a permanent log entry of who asked for it and why."""
    from database import resolve_approval, get_approvals, get_approval
    if payload.status not in ("Approved", "Rejected"):
        raise HTTPException(status_code=400, detail="status must be 'Approved' or 'Rejected'")
    if not resolve_approval(
        approval_id, payload.status, payload.resolved_by, payload.resolution_notes, payload.price_adjustment_percent
    ):
        raise HTTPException(status_code=404, detail="Approval not found")

    if payload.price_adjustment_percent:
        from data import apply_price_adjustment
        approval = get_approval(approval_id)
        reason = f"{approval['concern_type']} ({approval['routed_to']} — {payload.resolved_by}): {payload.resolution_notes or 'no notes'}"
        apply_price_adjustment(project_name, payload.price_adjustment_percent, reason)

    return get_approvals(project_name)

@app.get("/delivery-signoff/{project_name}")
async def api_get_delivery_signoff(project_name: str):
    from database import get_delivery_signoff
    record = get_delivery_signoff(project_name)
    return record or {"project_name": project_name, "status": "Pending", "signed_by": None, "signed_at": None, "notes": None}

class DeliverySignoffRequest(BaseModel):
    status: str  # 'Approved' | 'Rejected'
    signed_by: str = "Delivery Owner"
    notes: str = ""

@app.post("/delivery-signoff/{project_name}")
async def api_set_delivery_signoff(project_name: str, payload: DeliverySignoffRequest):
    """Records the delivery owner's final go/no-go on the submission-ready package. A rejection is
    meant to send the bid back to solution/resourcing/pricing with the notes attached — SOW Pilot
    records the notes here; routing the actual rework is a team process, not something the tool enforces."""
    from database import set_delivery_signoff, get_approvals, get_delivery_signoff, get_bid_qualification
    if payload.status not in ("Approved", "Rejected"):
        raise HTTPException(status_code=400, detail="status must be 'Approved' or 'Rejected'")

    if payload.status == "Approved":
        # The first gate in the workflow (should we even bid?) must be explicitly confirmed before
        # the last gate (ready to submit) can pass — otherwise a project can reach "ready to submit"
        # having never cleared qualification at all, or while qualification still shows No-Go.
        qualification = get_bid_qualification(project_name)
        qual_decision = qualification.get("decision") if qualification else None
        if qual_decision != "Go":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Bid qualification must be approved as 'Go' before sign-off. "
                    f"Current status: {qual_decision or 'qualification has not been run yet'}."
                )
            )

        pending = [a for a in get_approvals(project_name) if a["status"] == "Pending"]
        if pending:
            raise HTTPException(
                status_code=400,
                detail=f"{len(pending)} approval(s) are still pending — resolve them before signing off."
            )

    set_delivery_signoff(project_name, payload.status, payload.signed_by, payload.notes)
    return get_delivery_signoff(project_name)

@app.get("/pipeline")
async def api_get_pipeline():
    """Cross-project portfolio view — the thing an exec or delivery lead actually wants to see first,
    instead of opening 13 separate project pages one at a time. For each project, derives a single
    current stage from the signals already recorded elsewhere (qualification decision, pending
    approvals, proposal sends, contract status, win/loss), plus how many days it's been sitting there
    untouched — so a deal gone quiet is visible without anyone having to remember to check it.

    Also flags workers who are committed to more than one still-live project at once (cross-project
    double-booking) — something no single project's Resources tab can see on its own, since each only
    knows about its own team."""
    from database import (
        get_bid_qualification, get_approvals, get_contract_status, get_win_loss,
        get_db_workers
    )

    def _days_since(iso_ts: Optional[str]) -> Optional[int]:
        if not iso_ts:
            return None
        try:
            then = datetime.fromisoformat(iso_ts)
            return max(0, (datetime.now() - then).days)
        except Exception:
            return None

    projects = get_all_projects()
    rows = []
    total_pipeline_value = 0.0
    won_count = 0
    lost_count = 0

    for p in projects:
        overview = p.get("project_overview") or {}
        name = overview.get("project_name") or p.get("project_name")
        if not name:
            continue
        client = overview.get("client", "Unknown")
        budget = p.get("budget") or {}
        bid_price = budget.get("bid_price") or budget.get("total_cost") or 0

        qualification = get_bid_qualification(name)
        pending_approvals = [a for a in get_approvals(name) if a.get("status") == "Pending"]
        contract = get_contract_status(name)
        win_loss = get_win_loss(name)

        win_loss_status = (win_loss or {}).get("status")
        contract_status = (contract or {}).get("status", "Not Started")
        qual_decision = (qualification or {}).get("decision", "Pending")

        # Stage + the timestamp that actually reflects when this project last moved.
        if win_loss_status in ("Won", "Lost"):
            stage = win_loss_status
            last_activity = (win_loss or {}).get("decided_at")
        elif contract_status == "Signed":
            stage = "Contract Signed"
            last_activity = (contract or {}).get("updated_at")
        elif contract_status in ("Sent for Signature", "Rejected"):
            stage = f"Contract: {contract_status}"
            last_activity = (contract or {}).get("updated_at")
        elif qual_decision == "No-Go":
            stage = "No-Go"
            last_activity = (qualification or {}).get("decided_at")
        elif pending_approvals:
            stage = "Pending Approvals"
            last_activity = max((a.get("created_at") or "" for a in pending_approvals), default=None)
        elif qual_decision == "Go":
            stage = "Qualified — Proposal Not Yet Sent"
            last_activity = (qualification or {}).get("decided_at")
        else:
            stage = "Qualification"
            last_activity = p.get("processed_at")

        days_idle = _days_since(last_activity)
        # Stale thresholds reflect how long each stage can realistically sit before it signals neglect
        # rather than normal turnaround time (an approval sitting for a week is a problem; a signed
        # contract sitting for a week is just... signed).
        stale_after = {
            "Pending Approvals": 5,
            "Qualified — Proposal Not Yet Sent": 3,
            "Contract: Sent for Signature": 10,
        }.get(stage, None)
        is_stale = stale_after is not None and days_idle is not None and days_idle > stale_after

        if win_loss_status == "Won":
            won_count += 1
            total_pipeline_value += float(bid_price or 0)
        elif win_loss_status == "Lost":
            lost_count += 1
        else:
            total_pipeline_value += float(bid_price or 0)

        rows.append({
            "project_name": name,
            "client": client,
            "stage": stage,
            "bid_price": bid_price,
            "days_idle": days_idle,
            "is_stale": is_stale,
            "qualification_decision": qual_decision,
        })

    decided = won_count + lost_count
    win_rate = round((won_count / decided) * 100, 1) if decided else None

    # Cross-project resource conflicts: a worker showing up in assignments for more than one project
    # that hasn't itself been Lost/Rejected. This is a coarse "already committed elsewhere" signal,
    # not calendar-level week math — the system has no shared calendar dates across projects (phases
    # are tracked as relative week numbers per-project), so true overlap-of-weeks isn't computable yet.
    # Flagging the double-booking itself is still the real, high-value first catch in practice.
    closed_out = {r["project_name"] for r in rows if r["stage"] in ("Lost", "No-Go") or "Rejected" in r["stage"]}
    workers = get_db_workers()
    conflicts = []
    for w in workers:
        assignments = w.get("assignments") or []
        live_projects = sorted({
            a.get("projectName") for a in assignments
            if a.get("projectName") and a.get("projectName") not in closed_out
        })
        if len(live_projects) > 1:
            conflicts.append({
                "worker_id": w.get("id"),
                "worker_name": w.get("name"),
                "role": w.get("role"),
                "projects": live_projects,
            })

    return {
        "projects": rows,
        "summary": {
            "total_projects": len(rows),
            "total_pipeline_value": total_pipeline_value,
            "won": won_count,
            "lost": lost_count,
            "win_rate_percent": win_rate,
            "stale_count": sum(1 for r in rows if r["is_stale"]),
        },
        "resource_conflicts": conflicts,
    }

@app.on_event("startup")
async def startup_event():
    # Run the database migration task in the background to not block startup
    async def run_migration_in_background():
        await asyncio.sleep(2)  # Wait for server to bind
        from data import migrate_empty_budgets, deduplicate_projects, backfill_missing_requirement_versions
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, deduplicate_projects)
            await loop.run_in_executor(None, migrate_empty_budgets)
            await loop.run_in_executor(None, backfill_missing_requirement_versions)
        except Exception as e:
            print(f"[STARTUP MIGRATION ERROR] {e}")
            
    asyncio.create_task(run_migration_in_background())
    # Start automated background polling loop
    asyncio.create_task(gmail_polling_loop())

import uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
