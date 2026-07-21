import os
import uuid
import shutil
import asyncio
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pypdf import PdfReader
import io

from data import add_project, get_latest_project, get_dashboard_stats, get_all_projects
from orchestrator import run_visual_orchestrator
from agents import extract_requirements, allocate_resources, plan_timeline, estimate_costs, analyze_risks, generate_executive_report

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
                "attachment_name": file_id.split("_", 1)[-1]
            }
            # Append project record
            add_project(final_result)

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
            
            async def run_res(): return await loop.run_in_executor(None, allocate_resources, reqs)
            async def run_time(): return await loop.run_in_executor(None, plan_timeline, reqs)
            async def run_cost(): return await loop.run_in_executor(None, estimate_costs, reqs)
            async def run_risk(): return await loop.run_in_executor(None, analyze_risks, reqs)
            
            res_task = asyncio.create_task(run_res())
            time_task = asyncio.create_task(run_time())
            cost_task = asyncio.create_task(run_cost())
            risk_task = asyncio.create_task(run_risk())
            
            res, time, cost, risk = await asyncio.gather(res_task, time_task, cost_task, risk_task)
            report = await loop.run_in_executor(None, generate_executive_report, reqs, res, time, cost, risk)

            final_payload = {
                "project_overview": report.get("project_overview", {}),
                "executive_summary": report.get("executive_summary", ""),
                "technology_summary": report.get("technology_summary", {}),
                "resource_plan": report.get("resource_plan", {}),
                "timeline": report.get("timeline", {}),
                "budget": report.get("budget", {}),
                "risks": report.get("risks", []),
                "recommendations": report.get("recommendations", []),
                "overall_readiness_score": report.get("overall_readiness_score", 0),
                "processed_at": "Just now",
                "email_metadata": {
                    "sender": sender or "apex-delivery@gmail.com",
                    "subject": subject or "Apex SOW Ingestion",
                    "attachment_name": attachment_name or source_name
                }
            }

            add_project(final_payload)
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
    return get_all_projects()

@app.get("/dashboard")
async def get_dashboard():
    """Retrieve historical dashboard metrics."""
    return get_dashboard_stats()

@app.get("/test-groq")
async def test_groq():
    import traceback
    try:
        from groq import Groq
        k = os.getenv("GROQ_API_KEY")
        if not k or k == "YOUR_GROQ_API_KEY_HERE":
            return {"status": "error", "message": "Groq API key not set in environment or is default."}
        client = Groq(api_key=k)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": "Say hello"}
            ],
            model="llama-3.1-8b-instant"
        )
        return {"status": "success", "response": chat_completion.choices[0].message.content}
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

@app.on_event("startup")
async def startup_event():
    # Start the email polling loop as a background task
    asyncio.create_task(gmail_polling_loop())

import uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
