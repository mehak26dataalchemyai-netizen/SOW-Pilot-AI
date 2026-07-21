import os
import imaplib
import email
from email.header import decode_header
import io
import asyncio
from typing import List, Dict, Any, Tuple, Optional
import re
import html
from dotenv import load_dotenv
from pypdf import PdfReader

# Import python-docx
try:
    import docx
except ImportError:
    docx = None

from data import add_project, is_email_processed, mark_email_as_processed
from agents import (
    is_api_key_valid,
    split_sows_if_multiple,
    extract_requirements,
    allocate_resources,
    plan_timeline,
    estimate_costs,
    analyze_risks,
    generate_executive_report
)

load_dotenv(override=True)

gmail_scan_lock = asyncio.Lock()

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
        print(f"Error parsing PDF attachment: {e}")
        return ""

def parse_docx_bytes(docx_bytes: bytes) -> str:
    """Helper to parse raw DOCX bytes to text using python-docx."""
    if docx is None:
        print("[WARNING] python-docx not installed. Skipping DOCX parsing.")
        return ""
    try:
        doc = docx.Document(io.BytesIO(docx_bytes))
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text).strip()
    except Exception as e:
        print(f"Error parsing DOCX attachment: {e}")
        return ""

def parse_txt_bytes(txt_bytes: bytes) -> str:
    """Helper to parse raw TXT bytes to text."""
    try:
        return txt_bytes.decode('utf-8', errors='ignore').strip()
    except Exception as e:
        print(f"Error parsing TXT attachment: {e}")
        return ""

def get_gmail_credentials() -> Tuple[str, str]:
    """Load and return Gmail email and App Password."""
    email_user = os.getenv("GMAIL_EMAIL")
    email_pass = os.getenv("GMAIL_APP_PASSWORD")
    return email_user or "", email_pass or ""

def check_gmail_credentials() -> bool:
    """Check if Gmail configurations are populated."""
    user, pw = get_gmail_credentials()
    return user != "" and pw != "" and user != "YOUR_GMAIL_EMAIL_HERE" and pw != "YOUR_GMAIL_APP_PASSWORD_HERE"

async def process_sow_text(text: str, sender: str, subject: str, source_name: str) -> Dict[str, Any]:
    """Runs the full orchestrator agents pipeline for a single extracted SOW text block."""
    loop = asyncio.get_running_loop()
    
    # 1. Requirement Extraction
    reqs = await loop.run_in_executor(None, extract_requirements, text)
    
    # 2. Parallel Planning
    async def run_res(): return await loop.run_in_executor(None, allocate_resources, reqs)
    async def run_time(): return await loop.run_in_executor(None, plan_timeline, reqs)
    async def run_cost(): return await loop.run_in_executor(None, estimate_costs, reqs)
    async def run_risk(): return await loop.run_in_executor(None, analyze_risks, reqs)
    
    res_task = asyncio.create_task(run_res())
    time_task = asyncio.create_task(run_time())
    cost_task = asyncio.create_task(run_cost())
    risk_task = asyncio.create_task(run_risk())
    
    res, time, cost, risk = await asyncio.gather(res_task, time_task, cost_task, risk_task)
    
    # 3. Final synthesis
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
            "sender": sender,
            "subject": subject,
            "attachment_name": source_name
        }
    }
    
    # Persist the output
    add_project(final_payload)
    return final_payload

def clean_html(html_content: str) -> str:
    """Helper to remove script/style tags, strip HTML tags, and decode HTML entities."""
    try:
        # Remove script and style elements
        clean = re.sub(r'<(script|style).*?>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        # Strip all other HTML tags
        clean = re.sub(r'<[^>]+>', ' ', clean)
        # Replace multiple whitespace/newlines with single spaces
        clean = re.sub(r'\s+', ' ', clean)
        # Unescape HTML entities
        return html.unescape(clean).strip()
    except Exception as e:
        print(f"Error cleaning HTML: {e}")
        return html_content

async def scan_and_process_gmail_inbox() -> Dict[str, Any]:
    """
    Connects to Gmail, polls for unread messages, extracts SOW details
    from PDFs, Word Docs, plain text bodies, separates multi-SOW requests,
    runs the AI orchestrator on each, and marks the emails as read.
    """
    if gmail_scan_lock.locked():
        print("[GMAIL] Scan already in progress. Skipping concurrent run.")
        return {"status": "skipped", "message": "Another scan is already in progress."}
    async with gmail_scan_lock:
        return await _scan_and_process_gmail_inbox_under_lock()

async def _scan_and_process_gmail_inbox_under_lock() -> Dict[str, Any]:
    if not check_gmail_credentials():
        print("[GMAIL] Credentials not configured. Skipping Gmail scan.")
        return {"status": "skipped", "message": "Gmail credentials not set in .env."}

    email_user, email_pass = get_gmail_credentials()
    scanned_count = 0
    processed_sows_count = 0
    new_projects = []

    try:
        # Connect to Gmail via IMAP
        # Note: We must use standard SSL
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, email_pass)
        mail.select("inbox")
        
        # Search specifically for any emails containing "SOW" or "Statement of Work" in the subject
        # We run two searches to ensure maximum compatibility with different IMAP implementations
        msg_ids = []
        
        status1, search_data1 = mail.search(None, '(SUBJECT "SOW")')
        if status1 == "OK" and search_data1[0]:
            msg_ids.extend(search_data1[0].split())
            
        status2, search_data2 = mail.search(None, '(SUBJECT "Statement of Work")')
        if status2 == "OK" and search_data2[0]:
            msg_ids.extend(search_data2[0].split())
            
        # Remove duplicates from the search results while preserving order
        seen_ids = set()
        unique_msg_ids = []
        for mid in msg_ids:
            if mid not in seen_ids:
                seen_ids.add(mid)
                unique_msg_ids.append(mid)
        msg_ids = unique_msg_ids

        if not msg_ids:
            mail.close()
            mail.logout()
            return {"status": "success", "scanned_emails": 0, "processed_sows": 0, "projects": []}

        print(f"[GMAIL] Found {len(msg_ids)} potential SOW emails in inbox. Checking for new messages...")

        for msg_id in msg_ids:
            scanned_count += 1
            # Fetch message structure
            res_status, data = mail.fetch(msg_id, '(RFC822)')
            if res_status != "OK" or not data:
                continue

            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract Message-ID and check if already processed to avoid duplicates
            message_id = msg.get("Message-ID", "")
            if message_id and is_email_processed(message_id):
                continue
            
            # Extract Subject and Sender
            subject_header = decode_header(msg.get("Subject", "No Subject"))[0]
            subject = ""
            if isinstance(subject_header[0], bytes):
                subject = subject_header[0].decode(subject_header[1] or "utf-8", errors='ignore')
            else:
                subject = str(subject_header[0])

            sender_header = msg.get("From", "Unknown Sender")
            sender = ""
            sender_parts = decode_header(sender_header)
            for part, enc in sender_parts:
                if isinstance(part, bytes):
                    sender += part.decode(enc or "utf-8", errors='ignore')
                else:
                    sender += str(part)

            print(f"[GMAIL] Processing email {scanned_count}: Subject: '{subject}' from '{sender}'")

            email_body = ""
            html_body = ""
            attachments: List[Tuple[str, bytes]] = []

            # Walk email structure to find body text and attachments
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        # Extract email body text
                        payload = part.get_payload(decode=True)
                        if payload:
                            email_body += payload.decode('utf-8', errors='ignore') + "\n"
                    elif content_type == "text/html" and "attachment" not in content_disposition:
                        # Extract HTML body text
                        payload = part.get_payload(decode=True)
                        if payload:
                            html_body += payload.decode('utf-8', errors='ignore') + "\n"
                    elif "attachment" in content_disposition:
                        # Extract attachment file data
                        filename = part.get_filename()
                        if filename:
                            filename_parts = decode_header(filename)
                            cleaned_filename = ""
                            for fn_part, fn_enc in filename_parts:
                                if isinstance(fn_part, bytes):
                                    cleaned_filename += fn_part.decode(fn_enc or "utf-8", errors='ignore')
                                else:
                                    cleaned_filename += fn_part
                            file_data = part.get_payload(decode=True)
                            if file_data:
                                attachments.append((cleaned_filename, file_data))
            else:
                # Single part email
                content_type = msg.get_content_type()
                payload = msg.get_payload(decode=True)
                if content_type == "text/plain" and payload:
                    email_body = payload.decode('utf-8', errors='ignore')
                elif content_type == "text/html" and payload:
                    html_body = payload.decode('utf-8', errors='ignore')

            # Fall back to HTML body if plain text is empty or very short
            if not email_body.strip() or len(email_body.strip()) < 100:
                if html_body.strip():
                    cleaned_text = clean_html(html_body)
                    if len(cleaned_text) > len(email_body.strip()):
                        email_body = cleaned_text

            # Accumulate SOW texts to process from this email
            sows_to_process: List[Tuple[str, str]] = [] # list of (text, source_name)

            # A. Process Attachments first if present
            if attachments:
                for filename, data in attachments:
                    file_text = ""
                    lower_fn = filename.lower()
                    if lower_fn.endswith('.pdf'):
                        file_text = parse_pdf_bytes(data)
                    elif lower_fn.endswith('.docx'):
                        file_text = parse_docx_bytes(data)
                    elif lower_fn.endswith('.txt'):
                        file_text = parse_txt_bytes(data)
                    
                    if file_text and file_text.strip():
                        print(f"[GMAIL] Extracted SOW from attachment '{filename}' ({len(file_text)} chars).")
                        sows_to_process.append((file_text, filename))
            
            # B. If no attachments were found, check the email body text
            if not sows_to_process and email_body.strip():
                print(f"[GMAIL] No attachments found. Inspecting email body text...")
                # Run the separator agent to check for multiple SOWs in the body
                loop = asyncio.get_running_loop()
                split_texts = await loop.run_in_executor(None, split_sows_if_multiple, email_body)
                
                for idx, split_text in enumerate(split_texts):
                    if split_text.strip():
                        source = "Email Body text" if len(split_texts) == 1 else f"Email Body text (SOW {idx + 1})"
                        sows_to_process.append((split_text, source))

            # Execute orchestrator pipeline for each separated SOW
            if sows_to_process:
                print(f"[GMAIL] Running AI Orchestrator on {len(sows_to_process)} distinct SOWs found in this email...")
                for text, source in sows_to_process:
                    try:
                        processed_project = await process_sow_text(text, sender, subject, source)
                        new_projects.append({
                            "project_name": processed_project.get("project_overview", {}).get("project_name", "Unknown"),
                            "client": processed_project.get("project_overview", {}).get("client", "Unknown"),
                            "source": source
                        })
                        processed_sows_count += 1
                    except Exception as e:
                        print(f"[GMAIL] Failed to process SOW '{source}': {e}")
            else:
                print(f"[GMAIL] No readable SOW content (PDF, DOCX, TXT, or body text) found in email.")

            # Register email as processed in database to avoid duplicate ingestion
            if message_id:
                mark_email_as_processed(message_id)

            # Mark message as read
            mail.store(msg_id, '+FLAGS', '\\Seen')

        mail.close()
        mail.logout()
        return {
            "status": "success",
            "scanned_emails": scanned_count,
            "processed_sows": processed_sows_count,
            "projects": new_projects
        }

    except Exception as e:
        print(f"[GMAIL] Error during IMAP mailbox scan: {e}")
        return {"status": "error", "message": f"Gmail fetch failed: {str(e)}"}
