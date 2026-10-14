import os
import imaplib
import email
from email.header import decode_header
import io
import asyncio
import time
from typing import List, Dict, Any, Tuple, Optional
import re
from datetime import datetime
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
    generate_internal_bid_analysis,
    generate_client_proposal,
    generate_architecture_proposal,
    compute_simulation_status
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

async def process_sow_text(text: str, sender: str, subject: str, source_name: str, message_id: str = None) -> Dict[str, Any]:
    """Runs the full orchestrator agents pipeline for a single extracted SOW text block."""
    loop = asyncio.get_running_loop()
    
    # 1. Requirement Extraction
    reqs = await loop.run_in_executor(None, extract_requirements, text)

    if reqs.get("project_name"):
        from database import save_requirement_version
        await loop.run_in_executor(None, save_requirement_version, reqs["project_name"], 1, reqs)

    # 2. Resources, Risks & Architecture in parallel (all only need requirements)
    async def run_res(): return await loop.run_in_executor(None, allocate_resources, reqs)
    async def run_risk(): return await loop.run_in_executor(None, analyze_risks, reqs)
    async def run_arch(): return await loop.run_in_executor(None, generate_architecture_proposal, reqs)

    res_task = asyncio.create_task(run_res())
    risk_task = asyncio.create_task(run_risk())
    arch_task = asyncio.create_task(run_arch())

    res, risk, arch = await asyncio.gather(res_task, risk_task, arch_task)

    # 2b. Timeline needs the actual assigned team from resources above
    time = await loop.run_in_executor(None, plan_timeline, reqs, res)

    # Estimate budget based on the allocated resources, timeline, and risk-weighted contingency
    cost = await loop.run_in_executor(None, estimate_costs, reqs, res, time, risk)

    # 3. Final synthesis — internal analysis and the separate client-facing proposal
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
            "sender": sender,
            "subject": subject,
            "attachment_name": source_name,
            "message_id": message_id
        }
    }
    
    # Persist the output — run off the event loop since add_project() does blocking ChromaDB
    # indexing and compliance evaluation.
    await loop.run_in_executor(None, add_project, final_payload, text)
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

def _extract_body_and_attachments(msg) -> Tuple[str, List[Tuple[str, bytes]]]:
    """Walks a parsed email.message.Message to pull out the best available body text (preferring
    plain text, falling back to cleaned HTML) and any attachments. Shared by the inbound-SOW scanner
    and the thread-reply fetcher so both parse messages identically."""
    email_body = ""
    html_body = ""
    attachments: List[Tuple[str, bytes]] = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
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
            elif content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    email_body += payload.decode('utf-8', errors='ignore') + "\n"
            elif content_type == "text/html" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    html_body += payload.decode('utf-8', errors='ignore') + "\n"
    else:
        content_type = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if content_type == "text/plain" and payload:
            email_body = payload.decode('utf-8', errors='ignore')
        elif content_type == "text/html" and payload:
            html_body = payload.decode('utf-8', errors='ignore')

    if not email_body.strip() or len(email_body.strip()) < 100:
        if html_body.strip():
            cleaned_text = clean_html(html_body)
            if len(cleaned_text) > len(email_body.strip()):
                email_body = cleaned_text

    return email_body, attachments

def fetch_thread_reply(in_reply_to_message_id: str) -> Optional[str]:
    """Searches the inbox for a reply to a specific message we sent (matched via the In-Reply-To/
    References headers carrying OUR Message-ID, which send_reply_in_thread() sets explicitly) and
    returns its body text, or None if no reply has arrived yet. Synchronous/blocking — callers must
    run this via run_in_executor, same as the rest of the IMAP code in this module."""
    if not check_gmail_credentials() or not in_reply_to_message_id:
        return None

    email_user, email_pass = get_gmail_credentials()
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, email_pass)
        mail.select("inbox")

        # Try In-Reply-To first, then References — different mail clients populate these differently
        # when threading a reply.
        msg_ids = []
        for header_name in ("In-Reply-To", "References"):
            status, data = mail.search(None, f'(HEADER "{header_name}" "{in_reply_to_message_id}")')
            if status == "OK" and data[0]:
                msg_ids.extend(data[0].split())
            if msg_ids:
                break

        if not msg_ids:
            mail.close()
            mail.logout()
            return None

        # Most recent matching reply
        res_status, data = mail.fetch(msg_ids[-1], '(RFC822)')
        mail.close()
        mail.logout()
        if res_status != "OK" or not data:
            return None

        raw_email = data[0][1]
        reply_msg = email.message_from_bytes(raw_email)
        body, _ = _extract_body_and_attachments(reply_msg)
        return body.strip() or None
    except Exception as e:
        print(f"[GMAIL] Error fetching thread reply: {e}")
        return None

async def _scan_and_process_gmail_inbox_under_lock() -> Dict[str, Any]:
    if not check_gmail_credentials():
        print("[GMAIL] Credentials not configured. Skipping Gmail scan.")
        return {"status": "skipped", "message": "Gmail credentials not set in .env."}

    email_user, email_pass = get_gmail_credentials()
    scanned_count = 0
    processed_sows_count = 0
    new_projects = []
    loop = asyncio.get_running_loop()

    def _connect_and_search():
        """All the blocking IMAP setup (connect, login, select, search) in one synchronous call,
        run off the event loop — imaplib has no async variant, and calling it directly inside this
        async function was blocking the ENTIRE server (all requests, not just Gmail-related ones)
        for however long Gmail's IMAP server took to respond, every 30 seconds."""
        m = imaplib.IMAP4_SSL("imap.gmail.com")
        m.login(email_user, email_pass)
        m.select("inbox")

        ids = []
        status1, search_data1 = m.search(None, '(SUBJECT "SOW")')
        if status1 == "OK" and search_data1[0]:
            ids.extend(search_data1[0].split())
        status2, search_data2 = m.search(None, '(SUBJECT "Statement of Work")')
        if status2 == "OK" and search_data2[0]:
            ids.extend(search_data2[0].split())

        seen_ids = set()
        unique_ids = []
        for mid in ids:
            if mid not in seen_ids:
                seen_ids.add(mid)
                unique_ids.append(mid)
        return m, unique_ids

    try:
        mail, msg_ids = await loop.run_in_executor(None, _connect_and_search)

        if not msg_ids:
            await loop.run_in_executor(None, mail.close)
            await loop.run_in_executor(None, mail.logout)
            return {"status": "success", "scanned_emails": 0, "processed_sows": 0, "projects": []}

        print(f"[GMAIL] Found {len(msg_ids)} potential SOW emails in inbox. Checking for new messages...")

        for msg_id in msg_ids:
            scanned_count += 1
            # Fetch message structure
            res_status, data = await loop.run_in_executor(None, mail.fetch, msg_id, '(RFC822)')
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

            email_body, attachments = _extract_body_and_attachments(msg)

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
                        processed_project = await process_sow_text(text, sender, subject, source, message_id)
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
            await loop.run_in_executor(None, mail.store, msg_id, '+FLAGS', '\\Seen')

        await loop.run_in_executor(None, mail.close)
        await loop.run_in_executor(None, mail.logout)
        return {
            "status": "success",
            "scanned_emails": scanned_count,
            "processed_sows": processed_sows_count,
            "projects": new_projects
        }

    except Exception as e:
        print(f"[GMAIL] Error during IMAP mailbox scan: {e}")
        return {"status": "error", "message": f"Gmail fetch failed: {str(e)}"}

def send_proposal_email(to_email: str, project_name: str, client_name: str, budget_data: Dict[str, Any], timeline_weeks: str) -> Tuple[bool, str]:
    """
    Sends a formatted budget proposal email to the client using configured Gmail credentials.
    Falls back to a simulated success log if credentials are not configured.
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    email_user, email_pass = get_gmail_credentials()
    
    # Format budget breakdown html/text
    breakdown = budget_data.get("breakdown", budget_data)
    total_cost = budget_data.get("total_cost", 0)
    
    breakdown_rows = ""
    if isinstance(breakdown, dict):
        for category, value in breakdown.items():
            pretty_category = category.replace("_", " ").title()
            # If value is numeric, format it, otherwise use directly
            val_str = f"${value:,}" if isinstance(value, (int, float)) else str(value)
            breakdown_rows += f"<tr><td style='padding: 8px; border-bottom: 1px solid #ddd;'>{pretty_category}</td><td style='padding: 8px; border-bottom: 1px solid #ddd; text-align: right;'>{val_str}</td></tr>"
    
    formatted_total_cost = f"${total_cost:,}" if isinstance(total_cost, (int, float)) else str(total_cost)

    subject = f"Project Budget Proposal: {project_name} - {client_name}"
    
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <h2 style="color: #38a9f8; border-bottom: 2px solid #38a9f8; padding-bottom: 10px; margin-top: 0;">Project Budget Proposal</h2>
        <p>Dear {client_name} Team,</p>
        <p>Following our review of the Statement of Work (SOW) for <strong>{project_name}</strong>, we have prepared the estimated budget breakdown required for complete project delivery.</p>
        
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
          <thead>
            <tr style="background-color: #f8fafc;">
              <th style="padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0; color: #475569; font-size: 13px;">Cost Component</th>
              <th style="padding: 10px; text-align: right; border-bottom: 2px solid #e2e8f0; color: #475569; font-size: 13px;">Estimated Cost</th>
            </tr>
          </thead>
          <tbody>
            {breakdown_rows}
            <tr style="font-weight: bold; background-color: #f0f9ff; color: #0369a1;">
              <td style="padding: 12px 10px; border-top: 2px solid #38a9f8;">Total Project Cost</td>
              <td style="padding: 12px 10px; border-top: 2px solid #38a9f8; text-align: right; font-size: 16px;">{formatted_total_cost}</td>
            </tr>
          </tbody>
        </table>
        
        <p style="margin-top: 20px;"><strong>Timeline:</strong> {timeline_weeks}</p>
        <p>Please let us know if you approve this budget proposal so that we can assign workers and initiate sprint planning.</p>
        <br/>
        <p style="margin-bottom: 0;">Best regards,</p>
        <p style="margin-top: 5px; font-weight: bold; color: #0f172a;">SOWPilot AI Delivery Team</p>
      </body>
    </html>
    """
    
    if not check_gmail_credentials():
        print(f"[SIMULATED EMAIL] To: {to_email} | Subject: {subject}\n{html_content}")
        return True, "Simulated proposal sent successfully (Gmail credentials not set in .env)."

    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["From"] = email_user
        msg["To"] = to_email
        msg["Subject"] = subject
        
        msg.attach(MIMEText(html_content, "html"))
        
        # Send via SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email_user, email_pass)
        server.sendmail(email_user, to_email, msg.as_string())
        server.close()
        return True, "Proposal email sent successfully via Gmail."
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email: {e}")
        return False, f"Failed to send email: {str(e)}"

def extract_email_address(raw_sender: str) -> str:
    """Pulls a bare email address out of a 'Display Name <addr@domain.com>' style header,
    or returns the input unchanged if it's already a bare address."""
    if not raw_sender:
        return ""
    match = re.search(r"<([^>]+)>", raw_sender)
    return match.group(1).strip() if match else raw_sender.strip()

def compose_pre_bid_email_draft(project_name: str, client: str, questions: List[str]) -> Dict[str, str]:
    """Deterministically formats the still-pending pre-bid questions into a reviewable client email.
    Template-only (no LLM) — the questions themselves were already generated by the clarifying-questions
    agent, so this step is pure formatting, not content generation, and should be 100% reproducible."""
    client_name = client or "Team"
    numbered = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(questions))

    subject = f"Pre-Bid Clarification Questions — {project_name}"
    body = (
        f"Dear {client_name},\n\n"
        f"Thank you for the opportunity to review the Statement of Work for {project_name}. "
        f"Before finalizing our proposal, we would appreciate clarification on the following points:\n\n"
        f"{numbered}\n\n"
        f"We would be grateful for your response at your earliest convenience so we can ensure our proposal "
        f"fully addresses your requirements.\n\n"
        f"Best regards,\nDelivery Team"
    )
    return {"subject": subject, "body": body}

def compose_client_proposal_email(client_proposal: Dict[str, Any], project_name: str, client: str) -> Dict[str, str]:
    """Deterministically formats the generated client_proposal into a SHORT covering email — the full
    persuasive detail (why-us, solution, team, investment breakdown, timeline table, differentiators)
    lives in the attached formatted PDF, generated separately by proposal_pdf.generate_proposal_pdf().
    Template-only (no LLM) — the persuasive content itself was already written by generate_client_proposal();
    this step just assembles a scannable cover note that points to the attachment."""
    subject = f"Proposal: {project_name}"

    lines = []
    greeting = (client_proposal.get("client_greeting") or "").strip()
    if greeting:
        lines.append(greeting)
        lines.append("")

    lines.append(
        f"Please find our detailed proposal for {project_name} attached as a PDF, covering our approach, "
        "team, investment breakdown, and delivery timeline."
    )

    differentiators = client_proposal.get("differentiators") or []
    if differentiators:
        lines.append("")
        lines.append("A few highlights:")
        for d in differentiators[:4]:
            lines.append(f"  • {d}")

    next_steps = (client_proposal.get("next_steps") or "").strip()
    if next_steps:
        lines.append("")
        lines.append(next_steps)

    body = "\n".join(lines)
    return {"subject": subject, "body": body}

def send_reply_in_thread(
    to_email: str, subject: str, body: str, in_reply_to_message_id: str = None,
    attachment_bytes: bytes = None, attachment_filename: str = None,
) -> Tuple[bool, str, Optional[str]]:
    """Sends a plain-text email, threaded as a reply to the original message when a Message-ID is
    available (via In-Reply-To/References headers and a 'Re:' subject prefix, matching how real email
    clients thread replies) — so the client sees this as a continuation of the same conversation the
    SOW arrived on, not a disconnected new email.

    Optionally attaches a file (e.g. the formatted proposal PDF) — pass attachment_bytes with
    attachment_filename to include one.

    We generate and set OUR OWN Message-ID (rather than letting the SMTP server assign one silently)
    and return it, because a client's reply will carry this value back in its own In-Reply-To/References
    headers — that's the only reliable way to later find their reply in the inbox via fetch_thread_reply().
    Returns (success, message, our_message_id)."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.application import MIMEApplication
    from email.utils import make_msgid

    email_user, email_pass = get_gmail_credentials()

    if in_reply_to_message_id and not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    our_message_id = make_msgid(domain="sowpilot.ai")

    if not check_gmail_credentials():
        attach_note = f" [+ attachment: {attachment_filename}]" if attachment_bytes else ""
        print(f"[SIMULATED EMAIL] To: {to_email} | Subject: {subject}{attach_note}\n{body}")
        return True, "Simulated email sent successfully (Gmail credentials not set in .env).", our_message_id

    if not to_email or "@" not in to_email:
        return False, "No valid recipient email address available for this project.", None

    # "mixed" so a PDF attachment can ride alongside the text body — "alternative" is only for
    # multiple representations of the same content, not for attachments.
    msg = MIMEMultipart("mixed")
    msg["From"] = email_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Message-ID"] = our_message_id
    if in_reply_to_message_id:
        msg["In-Reply-To"] = in_reply_to_message_id
        msg["References"] = in_reply_to_message_id
    msg.attach(MIMEText(body, "plain"))
    if attachment_bytes and attachment_filename:
        part = MIMEApplication(attachment_bytes, _subtype="pdf")
        part.add_header("Content-Disposition", "attachment", filename=attachment_filename)
        msg.attach(part)

    # SMTP/TLS connections occasionally drop mid-handshake for transient network reasons unrelated
    # to our code (confirmed by reproducing an SSL EOF failure that then succeeded on immediate retry
    # with no changes). One automatic retry after a short pause covers that without masking a real,
    # persistent failure (e.g. bad credentials), which will still fail on the second attempt too.
    last_error = None
    for attempt in range(2):
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
            server.starttls()
            server.login(email_user, email_pass)
            server.sendmail(email_user, to_email, msg.as_string())
            server.close()
            return True, "Email sent successfully" + (" in the original thread." if in_reply_to_message_id else "."), our_message_id
        except Exception as e:
            last_error = e
            print(f"[EMAIL ERROR] Send attempt {attempt + 1} failed: {e}")
            if attempt == 0:
                time.sleep(2)

    return False, f"Failed to send email after 2 attempts: {str(last_error)}", None

def send_internal_notification(to_email: str, subject: str, body: str) -> Tuple[bool, str]:
    """Sends a standalone internal notification (e.g. an approval concern routed to a department) — not
    threaded to any client conversation, since this goes to internal staff, not the client. Reuses the
    same simulate-when-unconfigured and one-retry-on-transient-failure behavior as send_reply_in_thread."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    email_user, email_pass = get_gmail_credentials()

    if not check_gmail_credentials():
        print(f"[SIMULATED INTERNAL EMAIL] To: {to_email} | Subject: {subject}\n{body}")
        return True, "Simulated notification sent successfully (Gmail credentials not set in .env)."

    if not to_email or "@" not in to_email:
        return False, "No valid notification email address configured."

    msg = MIMEMultipart("mixed")
    msg["From"] = email_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    last_error = None
    for attempt in range(2):
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
            server.starttls()
            server.login(email_user, email_pass)
            server.sendmail(email_user, to_email, msg.as_string())
            server.close()
            return True, "Notification sent successfully."
        except Exception as e:
            last_error = e
            print(f"[EMAIL ERROR] Notification send attempt {attempt + 1} failed: {e}")
            if attempt == 0:
                time.sleep(2)

    return False, f"Failed to send notification after 2 attempts: {str(last_error)}"
