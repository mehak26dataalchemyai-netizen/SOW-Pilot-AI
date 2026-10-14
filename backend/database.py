import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sowpilot.db")

def get_db_connection():
    """Establish a connection to the SQLite database with dict factory row parsing."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize SQLite database tables, seed worker directory, and migrate projects_db.json."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Projects Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        project_name TEXT NOT NULL,
        client TEXT NOT NULL,
        budget REAL,
        target_budget TEXT,
        readiness_score INTEGER,
        budget_approved INTEGER DEFAULT 0,
        processed_at TEXT,
        full_data TEXT
    )
    """)

    # 2. Workers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workers (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        skills TEXT NOT NULL, -- JSON list
        status TEXT NOT NULL, -- 'Available' | 'Assigned'
        billing_rate REAL NOT NULL, -- hourly rate in USD
        assignments TEXT NOT NULL -- JSON list of {projectName, task}
    )
    """)

    # 3. Agent Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT,
        agent_name TEXT NOT NULL,
        action TEXT NOT NULL,
        reasoning TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    """)

    # 4. Policy Checks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS policy_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT,
        policy_name TEXT NOT NULL,
        passed INTEGER NOT NULL, -- 1 = True, 0 = False
        message TEXT NOT NULL
    )
    """)

    # 5. Evaluation Metrics Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT,
        metric_name TEXT NOT NULL,
        score REAL NOT NULL,
        reason TEXT
    )
    """)

    # 6. Processed Emails Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_emails (
        message_id TEXT PRIMARY KEY
    )
    """)

    # 7. Org Capabilities Table (the certifications/accreditations the org actually holds —
    # configurable data, not a hardcoded list inside the qualification logic)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS org_capabilities (
        certification TEXT PRIMARY KEY
    )
    """)

    # 8. Bid Qualifications Table (Go/No-Go recommendation + human decision per project)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bid_qualifications (
        project_name TEXT PRIMARY KEY,
        recommendation TEXT NOT NULL,
        blocking_issues TEXT NOT NULL, -- JSON list
        reasoning TEXT NOT NULL, -- JSON list
        required_certifications TEXT NOT NULL, -- JSON list
        missing_certifications TEXT NOT NULL, -- JSON list
        submission_deadline TEXT,
        pre_bid_question_deadline TEXT,
        deadline_status TEXT,
        decision TEXT DEFAULT 'Pending', -- 'Pending' | 'Go' | 'No-Go'
        decided_by TEXT,
        decided_at TEXT,
        assigned_delivery_owner TEXT,
        assigned_at TEXT,
        created_at TEXT NOT NULL
    )
    """)
    # Older databases created before this column existed — add it if missing (SQLite has no
    # "ADD COLUMN IF NOT EXISTS", so this is the standard pattern for additive migrations).
    cursor.execute("PRAGMA table_info(bid_qualifications)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    if "assigned_delivery_owner" not in existing_cols:
        cursor.execute("ALTER TABLE bid_qualifications ADD COLUMN assigned_delivery_owner TEXT")
    if "assigned_at" not in existing_cols:
        cursor.execute("ALTER TABLE bid_qualifications ADD COLUMN assigned_at TEXT")

    # 9. Requirement Versions Table (v1 = raw extraction, v2 = merged with pre-bid Q&A answers — never overwritten)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requirement_versions (
        project_name TEXT NOT NULL,
        version INTEGER NOT NULL,
        requirements TEXT NOT NULL, -- JSON
        created_at TEXT NOT NULL,
        PRIMARY KEY (project_name, version)
    )
    """)

    # 10. Pre-Bid Questions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pre_bid_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        question TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending', -- 'Pending' | 'Answered'
        client_answer TEXT,
        answered_at TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # 11. Approvals Table (flagged concerns routed to the right internal stakeholder)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        concern_type TEXT NOT NULL,
        description TEXT NOT NULL,
        routed_to TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending', -- 'Pending' | 'Approved' | 'Rejected'
        resolved_by TEXT,
        resolved_at TEXT,
        resolution_notes TEXT,
        price_adjustment_percent REAL,
        created_at TEXT NOT NULL
    )
    """)
    cursor.execute("PRAGMA table_info(approvals)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    if "price_adjustment_percent" not in existing_cols:
        cursor.execute("ALTER TABLE approvals ADD COLUMN price_adjustment_percent REAL")

    # 12. Delivery Owner Sign-Off Table (final gate before a project can be marked submission-ready)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS delivery_signoffs (
        project_name TEXT PRIMARY KEY,
        status TEXT NOT NULL DEFAULT 'Pending', -- 'Pending' | 'Approved' | 'Rejected'
        signed_by TEXT,
        signed_at TEXT,
        notes TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # 13. Org Settings Table (small key-value config store — e.g. default bid margin — so these
    # aren't hardcoded constants buried in the cost engine)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS org_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    # 14. Bid Documents Checklist (the supporting documents a bid must be submitted WITH — reference
    # letters, financials, BAA templates — distinct from certifications, which are standing accreditations)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bid_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        document_name TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending', -- 'Pending' | 'Ready' | 'Not Applicable'
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT
    )
    """)

    # 15. Delivery Owner Review Checkpoints — the delivery owner tracks along at each major stage
    # (solutioning, pricing) rather than only being brought in for the final submission-ready sign-off
    # (which already has its own table, delivery_signoffs).
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS delivery_owner_reviews (
        project_name TEXT NOT NULL,
        stage TEXT NOT NULL, -- 'solutioning' | 'pricing'
        reviewed_by TEXT NOT NULL,
        reviewed_at TEXT NOT NULL,
        notes TEXT,
        PRIMARY KEY (project_name, stage)
    )
    """)

    # 16. Content Library — reusable, pre-approved boilerplate (company overview, standard certifications
    # language, etc.) the client proposal agent can draw on for consistent messaging across proposals,
    # instead of inventing company descriptions fresh from scratch every single time.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS content_library (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        label TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # 17. Win/Loss Tracking — what actually happened to the bid after the proposal was sent. Nothing
    # upstream in the pipeline captures this; it's recorded here as a deliberate post-award checkpoint.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS win_loss (
        project_name TEXT PRIMARY KEY,
        status TEXT NOT NULL DEFAULT 'Pending', -- 'Pending' | 'Won' | 'Lost'
        reason TEXT,
        decided_by TEXT,
        decided_at TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # 18. Estimate vs Actual — captures real delivery numbers (logged manually, since no timesheet/actuals
    # feed exists yet) against the original estimate, so bid accuracy can be reviewed project over project.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_actuals (
        project_name TEXT PRIMARY KEY,
        actual_total_cost REAL,
        actual_duration_weeks REAL,
        notes TEXT,
        logged_by TEXT,
        logged_at TEXT NOT NULL
    )
    """)

    # 19. Cost of Bidding — internal hours spent preparing THIS bid (BD/solutioning time), independent of
    # whether it's won. Lets the org see what pursuing a bid actually costs internally, win or lose.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bid_cost_tracking (
        project_name TEXT PRIMARY KEY,
        internal_hours REAL NOT NULL,
        internal_hourly_rate REAL NOT NULL DEFAULT 150,
        notes TEXT,
        logged_by TEXT,
        logged_at TEXT NOT NULL
    )
    """)

    # 20. Approval Routing Contacts — maps the deterministic routed_to department (set by
    # flag_approval_concerns's keyword rules) to a real email address, so a flagged concern actually
    # notifies someone instead of only appearing silently in the Approvals tab.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS approval_contacts (
        department TEXT PRIMARY KEY,
        email TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # 21. Proposal Revisions — a history log of every time a proposal was sent for a project, plus an
    # optional note on what the client asked to change before the next round. This is NOT an automated
    # negotiation engine (no AI renegotiates terms) — it's the tracking layer that makes the manual
    # revise-and-resend cycle visible instead of each send silently overwriting the last.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proposal_revisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        version INTEGER NOT NULL,
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        client_feedback TEXT,
        sent_in_thread INTEGER NOT NULL DEFAULT 0,
        message_id TEXT,
        sent_at TEXT NOT NULL
    )
    """)
    cursor.execute("PRAGMA table_info(proposal_revisions)")
    if "message_id" not in {row[1] for row in cursor.fetchall()}:
        cursor.execute("ALTER TABLE proposal_revisions ADD COLUMN message_id TEXT")

    # 22. Contract & Signature Status — manual tracking of where the actual contract/SOW signature
    # process stands. This does NOT perform e-signature itself (that's a deliberate integrate-don't-build
    # call — see Documenso/OpenSign) — it's a status tracker so the lifecycle doesn't go dark between
    # "proposal sent" and "outcome logged."
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contract_status (
        project_name TEXT PRIMARY KEY,
        status TEXT NOT NULL DEFAULT 'Not Started', -- 'Not Started' | 'Sent for Signature' | 'Signed' | 'Rejected'
        notes TEXT,
        updated_by TEXT,
        updated_at TEXT NOT NULL
    )
    """)

    # 23. Timeline Revisions — a permanent log of every schedule disruption applied to a project's
    # delivery plan (a dependency delay, a scope change, a resource conflict, velocity variance). Mirrors
    # the price_adjustments log on budget: the shift itself is computed deterministically (critical-path
    # ripple through phases and resource_schedule), never guessed, and the resulting cost impact is
    # applied through the same traceable financial-adjustment mechanism as a negotiated price change.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS timeline_revisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        trigger_type TEXT NOT NULL, -- 'Dependency Delay' | 'Scope Change' | 'Resource Conflict' | 'Velocity Variance' | 'Other'
        affected_phase TEXT NOT NULL,
        delta_weeks REAL NOT NULL,
        reason TEXT,
        cost_impact REAL,
        applied_by TEXT,
        applied_at TEXT NOT NULL
    )
    """)

    conn.commit()

    # Seed Workers if table is empty
    cursor.execute("SELECT COUNT(*) FROM workers")
    if cursor.fetchone()[0] == 0:
        seed_workers(conn)
    else:
        conn.close()

    # Seed a starter org capability list if empty (editable later via the API — not hardcoded logic)
    conn2 = get_db_connection()
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT COUNT(*) FROM org_capabilities")
    if cursor2.fetchone()[0] == 0:
        for cert in ["SOC 2 Type II", "ISO 27001", "ISO 9001"]:
            cursor2.execute("INSERT OR IGNORE INTO org_capabilities (certification) VALUES (?)", (cert,))
        conn2.commit()

    cursor2.execute("SELECT COUNT(*) FROM org_settings")
    if cursor2.fetchone()[0] == 0:
        cursor2.execute("INSERT OR IGNORE INTO org_settings (key, value) VALUES ('default_margin_percent', '15')")
        conn2.commit()

    cursor2.execute("SELECT COUNT(*) FROM content_library")
    if cursor2.fetchone()[0] == 0:
        starter_entries = [
            ("Company Overview", "We are a technology delivery partner specializing in AI-driven platforms, "
             "cloud infrastructure, and enterprise system integration, with a track record of delivering "
             "complex, compliance-sensitive projects on time and within budget."),
            ("Standard Certifications Statement", "Our organization maintains SOC 2 Type II certification and "
             "follows industry-standard security practices across all client engagements, including encryption "
             "in transit and at rest, role-based access control, and regular third-party security audits."),
        ]
        for label, content in starter_entries:
            cursor2.execute(
                "INSERT INTO content_library (label, content, created_at) VALUES (?, ?, ?)",
                (label, content, datetime.now().isoformat())
            )
        conn2.commit()
    conn2.close()

    # Import existing projects from projects_db.json
    import_existing_projects()

def seed_workers(conn):
    """Seed the workers database with mock personnel aligned with the Hire-to-Retire domain."""
    cursor = conn.cursor()
    
    default_workers = [
        ("w1", "Sarah Connor", "Project Manager", ["Timeline Planning", "Risk Management", "Stakeholder Communication"], 120.0),
        ("w2", "John Doe", "Lead Frontend Developer", ["React 18", "TypeScript", "Tailwind CSS", "Recharts"], 100.0),
        ("w3", "Alice Smith", "Lead Backend / AI Engineer", ["Python 3.11", "FastAPI", "LangGraph", "Gemini AI Integration"], 130.0),
        ("w4", "Bob Johnson", "DevOps Engineer", ["AWS ECS / Fargate", "Docker", "VPC Networking", "GitHub Actions"], 110.0),
        ("w5", "Emma Watson", "QA Automation Engineer", ["Playwright", "API Integration Testing", "SOC 2 Auditing", "Jest"], 90.0),
        ("w6", "David Miller", "UX/UI Designer", ["Figma wireframing", "User flows", "Color harmony", "Design systems"], 85.0),
        ("w7", "Clara Oswald", "Database Administrator", ["PostgreSQL", "Query optimization", "Partitioning", "Database replication"], 115.0),
        ("w8", "Leo Fitz", "Scrum Master", ["Agile Ceremonies", "JIRA", "Conflict Resolution", "Velocity Tracking"], 95.0),
        ("w9", "Jemma Simmons", "Product Owner", ["Product Backlog", "User Stories", "Roadmapping", "Feature Prioritization"], 125.0),
        ("w10", "Bruce Wayne", "Business Analyst", ["Requirement Gathering", "Process mapping", "Gap Analysis", "UML modeling"], 105.0),
        ("w11", "Diana Prince", "Technical Writer", ["API Docs", "Markdown", "User Manuals", "GitBook editing"], 75.0),
        ("w12", "Tony Stark", "Security Analyst", ["Penetration testing", "IAM Roles", "SOC 2 compliance", "SSL/TLS configuration"], 140.0),
        ("w13", "Natasha Romanoff", "Legal & Compliance Specialist", ["SOW Auditing", "Contract clauses", "SLA reviews", "Liability limits"], 130.0),
        ("w14", "Steve Rogers", "Financial Analyst", ["Cost estimation", "Budget forecasting", "ROI modeling", "Contingency math"], 110.0),
        ("w15", "Thor Odinson", "Full Stack Developer", ["Node.js", "React", "MongoDB", "REST API design"], 105.0),

        # The 15 above cover one candidate per role. Real SOWs span far more roles than that, and
        # worker-matching needs multiple real candidates per common role to produce meaningfully
        # differentiated scores — a single generic match otherwise always "wins" by default regardless
        # of fit. The roster below adds breadth across technical, business, compliance, design, and
        # industry-domain specialties (healthcare, fintech, govtech, etc.), with several workers sharing
        # a role where that's realistic (e.g. two Scrum Masters, five Project Managers).
        ("w16", "Priya Natarajan", "Program Manager", ["Portfolio Governance", "Cross-Team Roadmapping", "Executive Reporting", "Risk Escalation"], 135.0),
        ("w17", "Marcus Chen", "Project Manager (Healthcare Delivery)", ["HIPAA-Aware Planning", "Clinical Stakeholder Management", "Epic Rollout Coordination", "Risk Register Ownership"], 125.0),
        ("w18", "Fatima Al-Sayed", "Project Manager (Agile Delivery)", ["Scrum/Kanban Hybrid", "Sprint Planning", "Burndown Tracking", "Stakeholder Communication"], 115.0),
        ("w19", "Declan O'Brien", "Engagement Lead / Client Partner", ["Client Relationship Management", "Contract Negotiation Support", "Delivery Accountability", "Executive Briefings"], 150.0),
        ("w20", "Mei Lin Tan", "Scrum Master", ["Agile Ceremonies", "Impediment Removal", "Team Coaching", "Jira/Azure DevOps"], 100.0),
        ("w21", "Oluwaseun Adeyemi", "Product Owner (Fintech)", ["Payments Domain Backlog", "User Story Writing", "Regulatory Feature Prioritization", "Stakeholder Alignment"], 128.0),
        ("w22", "Grace Kowalski", "Release Manager", ["Release Planning", "Change Advisory Boards", "Deployment Coordination", "Rollback Procedures"], 112.0),
        ("w23", "Rajesh Iyer", "Business Analyst (Healthcare)", ["Clinical Workflow Mapping", "HL7/FHIR Requirements", "Gap Analysis", "Stakeholder Interviews"], 108.0),
        ("w24", "Camille Dubois", "Business Analyst (Fintech)", ["Payments Workflow Analysis", "Regulatory Requirements Mapping", "Process Modeling", "BRD Authoring"], 110.0),
        ("w25", "Tariq Mahmood", "Data Analyst", ["SQL", "Power BI", "Statistical Analysis", "Dashboard Design"], 90.0),
        ("w26", "Hannah Schmidt", "Requirements Analyst", ["Elicitation Workshops", "Use Case Modeling", "Traceability Matrices", "UML"], 95.0),
        ("w27", "Victor Alves", "Process Improvement Consultant", ["Lean Six Sigma", "Workflow Re-engineering", "Change Impact Analysis", "KPI Design"], 115.0),
        ("w28", "Noah Bergström", "Solutions Architect (Cloud)", ["Multi-Cloud Architecture", "Microservices Design", "API Gateway Patterns", "Cost Optimization"], 155.0),
        ("w29", "Amara Nwosu", "Solutions Architect (Enterprise)", ["Enterprise Integration Patterns", "Legacy Modernization", "SOA/ESB", "TOGAF"], 150.0),
        ("w30", "Lucas Ferreira", "Technical Architect", ["System Design", "Domain-Driven Design", "Scalability Planning", "Code Review Standards"], 140.0),
        ("w31", "Isabella Romano", "Cloud Architect (AWS)", ["AWS Well-Architected Framework", "VPC Design", "IAM Policy Design", "Cost Governance"], 145.0),
        ("w32", "Dmitri Volkov", "Cloud Architect (Azure)", ["Azure Landing Zones", "Azure AD / Entra ID", "Hybrid Cloud Networking", "Bicep/ARM Templates"], 142.0),
        ("w33", "Aisha Rahman", "Frontend Developer (React)", ["React 18", "Redux Toolkit", "Component Libraries", "Web Accessibility (WCAG)"], 98.0),
        ("w34", "Benjamin Kessler", "Frontend Developer (Angular)", ["Angular", "RxJS", "NgRx", "Enterprise UI Patterns"], 97.0),
        ("w35", "Chidinma Eze", "Frontend Developer (Vue)", ["Vue 3", "Pinia", "Vite", "Composition API"], 92.0),
        ("w36", "Oscar Lindqvist", "UI Engineer (Design Systems)", ["Design Tokens", "Storybook", "Component Documentation", "Cross-Browser Testing"], 100.0),
        ("w37", "Yuki Tanaka", "Frontend Developer (Next.js/SSR)", ["Next.js", "Server-Side Rendering", "Edge Functions", "Performance Optimization"], 105.0),
        ("w38", "Kwame Asante", "Backend Developer (Node.js)", ["Node.js", "Express", "GraphQL", "Microservices"], 102.0),
        ("w39", "Elena Petrova", "Backend Developer (Python/Django)", ["Django", "Django REST Framework", "Celery", "PostgreSQL"], 100.0),
        ("w40", "Henrik Dahl", "Backend Developer (Java/Spring)", ["Java 17", "Spring Boot", "Spring Security", "Kafka"], 108.0),
        ("w41", "Sofia Morales", "Backend Developer (.NET/C#)", [".NET 8", "ASP.NET Core", "Entity Framework", "Azure Functions"], 104.0),
        ("w42", "Arjun Mehta", "Backend Developer (Go)", ["Go", "gRPC", "Concurrency Patterns", "High-Throughput Services"], 110.0),
        ("w43", "Leila Hosseini", "API Integration Engineer", ["REST/SOAP Integration", "Webhooks", "OAuth 2.0", "API Rate Limiting Design"], 96.0),
        ("w44", "Carlos Mendoza", "Full Stack Developer (MERN)", ["MongoDB", "Express", "React", "Node.js"], 103.0),
        ("w45", "Nadia Kowalczyk", "Full Stack Developer (Python/React)", ["Python/FastAPI", "React", "PostgreSQL", "Docker"], 106.0),
        ("w46", "Ethan Walsh", "Full Stack Developer (Ruby on Rails)", ["Ruby on Rails", "Hotwire/Turbo", "Sidekiq", "RSpec"], 99.0),
        ("w47", "Mia Johansson", "iOS Developer (Swift)", ["Swift", "SwiftUI", "Core Data", "App Store Release Process"], 112.0),
        ("w48", "Rahul Verma", "Android Developer (Kotlin)", ["Kotlin", "Jetpack Compose", "Coroutines", "Play Store Release Process"], 110.0),
        ("w49", "Zainab Yusuf", "React Native Developer", ["React Native", "Expo", "Native Module Bridging", "Cross-Platform QA"], 105.0),
        ("w50", "Daniel Ostrowski", "Machine Learning Engineer", ["PyTorch", "Model Deployment", "Feature Engineering", "MLOps"], 145.0),
        ("w51", "Simone Laurent", "Data Scientist", ["Python/Pandas", "Statistical Modeling", "A/B Testing", "scikit-learn"], 138.0),
        ("w52", "Takeshi Nakamura", "Data Engineer", ["Apache Spark", "Airflow", "Data Warehousing", "ETL Pipeline Design"], 130.0),
        ("w53", "Adaeze Okonkwo", "NLP / AI Engineer", ["Large Language Models", "Prompt Engineering", "Vector Databases", "RAG Architecture"], 148.0),
        ("w54", "Felix Brandt", "Data Architect", ["Data Modeling", "Master Data Management", "Data Governance", "Schema Design"], 142.0),
        ("w55", "Ingrid Larsen", "Analytics Engineer", ["dbt", "SQL Transformation Pipelines", "BI Modeling", "Data Quality Testing"], 118.0),
        ("w56", "Youssef Benali", "DevOps Engineer (Azure)", ["Azure DevOps Pipelines", "Terraform", "Kubernetes (AKS)", "Monitoring (Azure Monitor)"], 115.0),
        ("w57", "Claire Fontaine", "DevOps Engineer (GCP)", ["GCP Cloud Build", "GKE", "Cloud Monitoring", "Infrastructure as Code"], 116.0),
        ("w58", "Ravi Shankar", "Site Reliability Engineer", ["Incident Response", "SLO/SLI Design", "Chaos Engineering", "Observability (Prometheus/Grafana)"], 132.0),
        ("w59", "Bjorn Eriksson", "Cloud Infrastructure Engineer", ["AWS/Azure Hybrid Infra", "VPN/Direct Connect", "Cost Monitoring", "Disaster Recovery Planning"], 118.0),
        ("w60", "Patricia Nkemelu", "Network Engineer", ["VPC Peering", "Firewall Configuration", "Load Balancer Design", "DNS Management"], 108.0),
        ("w61", "Omar Farouk", "QA Automation Engineer (Selenium)", ["Selenium WebDriver", "TestNG", "CI Test Pipelines", "Cross-Browser Automation"], 88.0),
        ("w62", "Beatrix Novak", "Manual QA Tester", ["Exploratory Testing", "Test Case Design", "Regression Testing", "Bug Triage"], 65.0),
        ("w63", "Santiago Rojas", "Performance Test Engineer", ["JMeter", "Load Testing", "Performance Profiling", "Bottleneck Analysis"], 100.0),
        ("w64", "Harriet Boateng", "Security Test Engineer / Penetration Tester", ["OWASP Top 10", "Burp Suite", "Vulnerability Scanning", "Pen Test Reporting"], 135.0),
        ("w65", "Luca Bianchi", "Accessibility Testing Specialist", ["WCAG 2.2 AA Auditing", "Screen Reader Testing", "Assistive Technology QA", "Accessibility Remediation"], 92.0),
        ("w66", "Monica Reyes", "HIPAA Compliance Specialist", ["HIPAA Risk Assessments", "BAA Review", "PHI Handling Policy", "Breach Response Planning"], 125.0),
        ("w67", "Andrei Popescu", "SOC 2 Compliance Auditor", ["SOC 2 Type II Audits", "Control Mapping", "Evidence Collection", "Audit Readiness"], 128.0),
        ("w68", "Charlotte Reid", "GDPR / Privacy Officer", ["Data Protection Impact Assessments", "GDPR Compliance", "Consent Management", "Cross-Border Data Transfer"], 130.0),
        ("w69", "Pedro Alvarez", "Risk & Compliance Analyst", ["Risk Register Management", "Regulatory Change Tracking", "Internal Controls Testing", "Audit Support"], 112.0),
        ("w70", "Wei Zhang", "Information Security Engineer", ["SIEM Management", "Identity & Access Management", "Encryption Standards", "Incident Response"], 138.0),
        ("w71", "Freya Hansen", "UX Researcher", ["User Interviews", "Usability Testing", "Journey Mapping", "Survey Design"], 95.0),
        ("w72", "Gabriel Souza", "Graphic Designer", ["Brand Identity", "Illustration", "Marketing Collateral", "Adobe Creative Suite"], 70.0),
        ("w73", "Anjali Desai", "Healthcare UX Designer", ["Clinical Workflow UX", "EHR-Adjacent Interfaces", "Patient-Facing Design", "Accessibility in Healthcare UX"], 98.0),
        ("w74", "Milo Jensen", "Product Designer", ["End-to-End Product Design", "Design Systems", "Prototyping (Figma)", "Design Critique Facilitation"], 102.0),
        ("w75", "Keisha Williams", "Epic / FHIR Integration Specialist", ["Epic EHR APIs", "HL7 FHIR", "Sandbox-to-Production Credentialing", "Healthcare Interoperability"], 150.0),
        ("w76", "Antoine Girard", "Fintech / Payments Specialist", ["PCI-DSS", "Payment Gateway Integration", "Fraud Detection Systems", "Open Banking APIs"], 140.0),
        ("w77", "Linda Osei", "E-commerce Platform Specialist", ["Shopify/Magento Architecture", "Checkout Optimization", "Inventory Sync", "Payment Gateway Config"], 105.0),
        ("w78", "Hassan Qureshi", "Supply Chain & Manufacturing Specialist", ["ERP Integration", "IoT Sensor Data", "Inventory Forecasting", "Logistics Workflow Design"], 115.0),
        ("w79", "Emilia Costa", "EdTech Specialist", ["LMS Integration", "SCORM/xAPI Standards", "Student Data Privacy (FERPA)", "Accessibility for Learning Platforms"], 100.0),
        ("w80", "George Whitfield", "GovTech / Public Sector Specialist", ["FedRAMP Awareness", "Section 508 Compliance", "Public Sector Procurement Process", "Accessibility Standards"], 120.0),
        ("w81", "Valentina Russo", "Legal Tech Specialist", ["Contract Lifecycle Management Tools", "E-Discovery Platforms", "Legal Workflow Automation", "Document Management Systems"], 118.0),
        ("w82", "Samuel Okafor", "Insurance & Actuarial Specialist", ["Claims Processing Systems", "Actuarial Data Modeling", "Underwriting Workflow", "Insurance Regulatory Compliance"], 122.0),
        ("w83", "Natalia Kowalski", "Real Estate PropTech Specialist", ["Property Management Systems", "MLS Integration", "Lease Management Workflow", "Real Estate Transaction Platforms"], 108.0),
        ("w84", "Ibrahim Al-Farsi", "Energy & Utilities Specialist", ["SCADA Systems Awareness", "Smart Metering Data", "Utility Billing Systems", "Regulatory Reporting (Energy Sector)"], 125.0),
        ("w85", "Rosa Jimenez", "Instructional Designer / Trainer", ["Curriculum Design", "Adult Learning Theory", "Training Material Development", "LMS Authoring Tools"], 90.0),
        ("w86", "Sven Karlsson", "Localization & Translation Specialist", ["Multi-Language Content Management", "Translation Memory Tools", "Cultural Adaptation", "i18n/l10n Workflow"], 85.0),
        ("w87", "Yasmin Khalil", "Content Strategist", ["Content Architecture", "Editorial Guidelines", "SEO-Aware Writing", "Content Governance"], 88.0),
        ("w88", "Connor Murphy", "Customer Support Lead", ["Support Ticket Triage", "Escalation Management", "SLA Monitoring", "Knowledge Base Curation"], 80.0),
        ("w89", "Aaliyah Brooks", "Change Management Consultant", ["Organizational Change Planning", "Stakeholder Readiness Assessment", "Training Rollout Coordination", "Adoption Metrics"], 118.0),
        ("w90", "Mateus Pereira", "Implementation Specialist", ["Client Onboarding", "Data Migration Coordination", "System Configuration", "Go-Live Support"], 95.0),
        ("w91", "Nora Fischer", "Help Desk / L1 Support Engineer", ["Ticketing Systems", "Basic Troubleshooting", "User Account Administration", "Issue Documentation"], 60.0),
        ("w92", "Jonas Weber", "Procurement Specialist", ["Vendor Sourcing", "RFP Management", "Contract Negotiation Support", "Purchase Order Workflow"], 100.0),
        ("w93", "Chiara Esposito", "Contracts Manager", ["Contract Drafting Support", "SOW Redlining", "Terms Negotiation Tracking", "Contract Repository Management"], 120.0),
        ("w94", "Olivia Bennett", "HR / People Ops Consultant", ["Staffing Plan Support", "Onboarding Process Design", "Resource Allocation Policy", "Team Structure Advisory"], 105.0),
        ("w95", "Tomás Herrera", "Vendor Management Specialist", ["Vendor Performance Tracking", "SLA Compliance Monitoring", "Third-Party Risk Assessment", "Vendor Relationship Management"], 98.0),
        ("w96", "Isabel Castillo", "Marketing Specialist", ["Campaign Planning", "Marketing Analytics", "Brand Messaging", "Launch Coordination"], 85.0),
        ("w97", "Liam O'Sullivan", "SEO / Content Specialist", ["Technical SEO", "Keyword Research", "Content Optimization", "Analytics Reporting"], 78.0),
        ("w98", "Priyanka Rao", "Digital Campaign Manager", ["Paid Media Strategy", "Marketing Automation", "Conversion Tracking", "A/B Testing (Campaigns)"], 95.0),
        ("w99", "Erik Nilsson", "Database Developer (NoSQL/MongoDB)", ["MongoDB Schema Design", "Aggregation Pipelines", "Sharding Strategy", "Index Optimization"], 100.0),
        ("w100", "Fatou Diallo", "Data Warehouse Engineer", ["Snowflake/Redshift", "Star Schema Design", "ELT Pipelines", "Query Performance Tuning"], 115.0),
    ]

    for w_id, name, role, skills, rate in default_workers:
        cursor.execute(
            "INSERT INTO workers (id, name, role, skills, status, billing_rate, assignments) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (w_id, name, role, json.dumps(skills), "Available", rate, json.dumps([]))
        )
    
    conn.commit()
    conn.close()
    print("[DATABASE] SQLite database initialized and seeded with workers.")

def import_existing_projects():
    """Migrate projects from projects_db.json into SQLite if they aren't already imported."""
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects_db.json")
    if not os.path.exists(json_path):
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        projects = data.get("projects", [])
        if not projects:
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        migrated_count = 0

        for p in projects:
            overview = p.get("project_overview") or {}
            proj_name = overview.get("project_name") or p.get("project_name", "Unknown")
            client = overview.get("client") or p.get("client", "Unknown")
            
            p_id = p.get("id")
            if not p_id:
                p_id = f"{proj_name.lower().replace(' ', '_')}_{client.lower().replace(' ', '_')}"
                p["id"] = p_id

            # Check if project exists in database
            cursor.execute("SELECT 1 FROM projects WHERE id = ?", (p_id,))
            if cursor.fetchone() is not None:
                continue

            # Calculate total cost
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

            client_budget = overview.get("client_stated_budget")
            if client_budget and client_budget not in ("Not specified", "Not Specified"):
                target_budget = client_budget
            else:
                target_budget = overview.get("budget") or p.get("target_budget", "Not Specified")
            readiness_score = p.get("overall_readiness_score", 0)
            approved = 1 if p.get("budget_approved") else 0
            processed_at = p.get("processed_at") or datetime.now().strftime("%b %d, %Y %I:%M %p")

            # Insert into database
            cursor.execute("""
                INSERT INTO projects (id, project_name, client, budget, target_budget, readiness_score, budget_approved, processed_at, full_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (p_id, proj_name, client, budget_amount, target_budget, readiness_score, approved, processed_at, json.dumps(p)))
            conn.commit()

            # Generate evaluations, compliance metrics and audit logs for this project
            try:
                from compliance import evaluate_and_audit_project
                evaluate_and_audit_project(p)
            except Exception as e:
                print(f"[MIGRATION WARNING] Failed to evaluate project {proj_name}: {e}")
            
            migrated_count += 1

        conn.close()
        if migrated_count > 0:
            print(f"[DATABASE] Successfully migrated {migrated_count} existing projects from projects_db.json to SQLite.")
    except Exception as e:
        print(f"[DATABASE ERROR] Migration of projects_db.json failed: {e}")

# --- Database Query API ---

def add_audit_log(project_name: str, agent_name: str, action: str, reasoning: str):
    """Add a record to the audit trail log."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_logs (project_name, agent_name, action, reasoning, timestamp) VALUES (?, ?, ?, ?, ?)",
        (project_name, agent_name, action, reasoning, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_audit_logs(project_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve audit logs, optionally filtered by project name."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if project_name:
        cursor.execute("SELECT * FROM audit_logs WHERE project_name = ? ORDER BY id ASC", (project_name,))
    else:
        cursor.execute("SELECT * FROM audit_logs ORDER BY id ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def add_policy_check(project_name: str, policy_name: str, passed: bool, message: str):
    """Add or update a policy compliance record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM policy_checks WHERE project_name = ? AND policy_name = ?", (project_name, policy_name))
    row = cursor.fetchone()
    if row:
        cursor.execute(
            "UPDATE policy_checks SET passed = ?, message = ? WHERE id = ?",
            (1 if passed else 0, message, row["id"])
        )
    else:
        cursor.execute(
            "INSERT INTO policy_checks (project_name, policy_name, passed, message) VALUES (?, ?, ?, ?)",
            (project_name, policy_name, 1 if passed else 0, message)
        )
    conn.commit()
    conn.close()

def get_policy_checks(project_name: str) -> List[Dict[str, Any]]:
    """Retrieve policy compliance metrics for a project."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM policy_checks WHERE project_name = ?", (project_name,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def add_evaluation(project_name: str, metric_name: str, score: float, reason: str):
    """Add or update an LLM system evaluation score."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM evaluations WHERE project_name = ? AND metric_name = ?", (project_name, metric_name))
    row = cursor.fetchone()
    if row:
        cursor.execute(
            "UPDATE evaluations SET score = ?, reason = ? WHERE id = ?",
            (score, reason, row["id"])
        )
    else:
        cursor.execute(
            "INSERT INTO evaluations (project_name, metric_name, score, reason) VALUES (?, ?, ?, ?)",
            (project_name, metric_name, score, reason)
        )
    conn.commit()
    conn.close()

def get_evaluations(project_name: str) -> List[Dict[str, Any]]:
    """Retrieve system evaluation metrics for a project."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM evaluations WHERE project_name = ?", (project_name,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_db_workers() -> List[Dict[str, Any]]:
    """Fetch all workers from the HR directory."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workers")
    rows = []
    for r in cursor.fetchall():
        row = dict(r)
        row["skills"] = json.loads(row["skills"])
        row["assignments"] = json.loads(row["assignments"])
        rows.append(row)
    conn.close()
    return rows

def add_db_worker(w: Dict[str, Any]):
    """Add a new worker into the HR database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO workers (id, name, role, skills, status, billing_rate, assignments) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            w.get("id"),
            w.get("name"),
            w.get("role"),
            json.dumps(w.get("skills", [])),
            w.get("status", "Available"),
            float(w.get("billing_rate", 100.0)),
            json.dumps(w.get("assignments", []))
        )
    )
    conn.commit()
    conn.close()

def update_worker_status(w_id: str, status: str, assignments: List[Dict[str, Any]]):
    """Update a worker's availability and assignment status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE workers SET status = ?, assignments = ? WHERE id = ?",
        (status, json.dumps(assignments), w_id)
    )
    conn.commit()
    conn.close()

def delete_db_worker(w_id: str):
    """Remove a worker from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM workers WHERE id = ?", (w_id,))
    conn.commit()
    conn.close()

def is_email_processed_db(message_id: str) -> bool:
    """Check if email has been ingested."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM processed_emails WHERE message_id = ?", (message_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def mark_email_as_processed_db(message_id: str):
    """Register email as processed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO processed_emails (message_id) VALUES (?)", (message_id,))
        conn.commit()
    except Exception:
        pass
    conn.close()

# --- Org Capabilities (certifications the org actually holds) ---

def get_org_capabilities() -> List[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT certification FROM org_capabilities ORDER BY certification ASC")
    rows = [r["certification"] for r in cursor.fetchall()]
    conn.close()
    return rows

def add_org_capability(certification: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO org_capabilities (certification) VALUES (?)", (certification.strip(),))
    conn.commit()
    conn.close()

def remove_org_capability(certification: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM org_capabilities WHERE certification = ?", (certification,))
    conn.commit()
    conn.close()

# --- Bid Qualifications ---

def save_bid_qualification(project_name: str, qual: Dict[str, Any]):
    """Insert or refresh the Go/No-Go recommendation for a project. Re-running qualification
    resets the decision back to Pending, since the underlying facts may have changed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bid_qualifications
            (project_name, recommendation, blocking_issues, reasoning, required_certifications,
             missing_certifications, submission_deadline, pre_bid_question_deadline, deadline_status,
             decision, decided_by, decided_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', NULL, NULL, ?)
        ON CONFLICT(project_name) DO UPDATE SET
            recommendation=excluded.recommendation,
            blocking_issues=excluded.blocking_issues,
            reasoning=excluded.reasoning,
            required_certifications=excluded.required_certifications,
            missing_certifications=excluded.missing_certifications,
            submission_deadline=excluded.submission_deadline,
            pre_bid_question_deadline=excluded.pre_bid_question_deadline,
            deadline_status=excluded.deadline_status,
            decision='Pending', decided_by=NULL, decided_at=NULL
    """, (
        project_name, qual.get("recommendation"), json.dumps(qual.get("blocking_issues", [])),
        json.dumps(qual.get("reasoning", [])), json.dumps(qual.get("required_certifications", [])),
        json.dumps(qual.get("missing_certifications", [])), qual.get("submission_deadline"),
        qual.get("pre_bid_question_deadline"), qual.get("deadline_status"),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def get_bid_qualification(project_name: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bid_qualifications WHERE project_name = ?", (project_name,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    for field in ["blocking_issues", "reasoning", "required_certifications", "missing_certifications"]:
        try:
            d[field] = json.loads(d[field]) if d[field] else []
        except (json.JSONDecodeError, TypeError):
            d[field] = []
    return d

def set_bid_decision(project_name: str, decision: str, decided_by: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE bid_qualifications SET decision = ?, decided_by = ?, decided_at = ? WHERE project_name = ?",
        (decision, decided_by, datetime.now().isoformat(), project_name)
    )
    conn.commit()
    conn.close()

def assign_delivery_owner(project_name: str, owner_name: str) -> bool:
    """Records who will own delivery of this project from the moment it's qualified — not just at
    final sign-off — so the same person tracks solutioning/pricing as it develops (per stakeholder
    feedback: bringing the delivery owner in only at the end causes conflict post-win)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE bid_qualifications SET assigned_delivery_owner = ?, assigned_at = ? WHERE project_name = ?",
        (owner_name, datetime.now().isoformat(), project_name)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

# --- Org Settings (small key-value config, e.g. default bid margin) ---

def get_org_setting(key: str, default: str = None) -> Optional[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM org_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default

def set_org_setting(key: str, value: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO org_settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, value))
    conn.commit()
    conn.close()

# --- Requirement Versions (v1 raw extraction, v2 merged with pre-bid Q&A — never overwritten) ---

def save_requirement_version(project_name: str, version: int, requirements: Dict[str, Any]):
    """Version 1 (the raw extraction) is write-once — re-ingestion attempts are ignored so the original
    snapshot is never silently altered. Version 2+ (post pre-bid Q&A) is expected to be re-derived as more
    questions get answered, so it upserts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if version == 1:
        cursor.execute(
            "INSERT OR IGNORE INTO requirement_versions (project_name, version, requirements, created_at) VALUES (?, ?, ?, ?)",
            (project_name, version, json.dumps(requirements), datetime.now().isoformat())
        )
    else:
        cursor.execute("""
            INSERT INTO requirement_versions (project_name, version, requirements, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(project_name, version) DO UPDATE SET
                requirements=excluded.requirements, created_at=excluded.created_at
        """, (project_name, version, json.dumps(requirements), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_requirement_version(project_name: str, version: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT requirements FROM requirement_versions WHERE project_name = ? AND version = ?",
        (project_name, version)
    )
    row = cursor.fetchone()
    conn.close()
    return json.loads(row["requirements"]) if row else None

def get_latest_requirement_version(project_name: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT requirements FROM requirement_versions WHERE project_name = ? ORDER BY version DESC LIMIT 1",
        (project_name,)
    )
    row = cursor.fetchone()
    conn.close()
    return json.loads(row["requirements"]) if row else None

# --- Pre-Bid Questions ---

def add_pre_bid_question(project_name: str, question: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO pre_bid_questions (project_name, question, status, created_at) VALUES (?, ?, 'Pending', ?)",
        (project_name, question, datetime.now().isoformat())
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def clear_pending_pre_bid_questions(project_name: str):
    """Removes not-yet-answered questions before a regenerate, so re-running doesn't pile up duplicates.
    Already-answered questions are preserved as a permanent record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pre_bid_questions WHERE project_name = ? AND status = 'Pending'", (project_name,))
    conn.commit()
    conn.close()

def get_pre_bid_questions(project_name: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pre_bid_questions WHERE project_name = ? ORDER BY id ASC", (project_name,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def answer_pre_bid_question(question_id: int, client_answer: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE pre_bid_questions SET status = 'Answered', client_answer = ?, answered_at = ? WHERE id = ?",
        (client_answer, datetime.now().isoformat(), question_id)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

# --- Approvals ---

def add_approval(project_name: str, concern_type: str, description: str, routed_to: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO approvals (project_name, concern_type, description, routed_to, status, created_at) "
        "VALUES (?, ?, ?, ?, 'Pending', ?)",
        (project_name, concern_type, description, routed_to, datetime.now().isoformat())
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def clear_pending_approvals(project_name: str):
    """Removes not-yet-resolved approvals before a regenerate. Resolved ones are preserved as a record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM approvals WHERE project_name = ? AND status = 'Pending'", (project_name,))
    conn.commit()
    conn.close()

def get_approvals(project_name: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM approvals WHERE project_name = ? ORDER BY id ASC", (project_name,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def resolve_approval(approval_id: int, status: str, resolved_by: str, resolution_notes: str = "",
                      price_adjustment_percent: float = None) -> bool:
    """price_adjustment_percent lets a stakeholder's resolution actually move the price (e.g. Finance
    saying 'approved, but add 3% for Net-90 cost-of-money') instead of being trapped in free-text notes
    that never reach the cost model."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE approvals SET status = ?, resolved_by = ?, resolved_at = ?, resolution_notes = ?, "
        "price_adjustment_percent = ? WHERE id = ?",
        (status, resolved_by, datetime.now().isoformat(), resolution_notes, price_adjustment_percent, approval_id)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

def get_approval(approval_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# --- Delivery Owner Sign-Off ---

def get_delivery_signoff(project_name: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM delivery_signoffs WHERE project_name = ?", (project_name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def set_delivery_signoff(project_name: str, status: str, signed_by: str, notes: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO delivery_signoffs (project_name, status, signed_by, signed_at, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(project_name) DO UPDATE SET
            status=excluded.status, signed_by=excluded.signed_by,
            signed_at=excluded.signed_at, notes=excluded.notes
    """, (project_name, status, signed_by, datetime.now().isoformat(), notes, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# --- Bid Documents Checklist ---

def seed_bid_documents(project_name: str, document_names: List[str]):
    """Adds any required bid documents not already tracked for this project. Safe to call repeatedly —
    skips document names that already exist so re-visiting the tab doesn't create duplicates."""
    if not document_names:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT document_name FROM bid_documents WHERE project_name = ?", (project_name,))
    existing = {r["document_name"] for r in cursor.fetchall()}
    now = datetime.now().isoformat()
    for doc_name in document_names:
        if doc_name not in existing:
            cursor.execute(
                "INSERT INTO bid_documents (project_name, document_name, status, created_at) VALUES (?, ?, 'Pending', ?)",
                (project_name, doc_name, now)
            )
    conn.commit()
    conn.close()

def get_bid_documents(project_name: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bid_documents WHERE project_name = ? ORDER BY id ASC", (project_name,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def update_bid_document_status(doc_id: int, status: str, notes: str = "") -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE bid_documents SET status = ?, notes = ?, updated_at = ? WHERE id = ?",
        (status, notes, datetime.now().isoformat(), doc_id)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

# --- Delivery Owner Review Checkpoints (solutioning, pricing — tracked along the way, not just at the end) ---

def set_delivery_owner_review(project_name: str, stage: str, reviewed_by: str, notes: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO delivery_owner_reviews (project_name, stage, reviewed_by, reviewed_at, notes)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(project_name, stage) DO UPDATE SET
            reviewed_by=excluded.reviewed_by, reviewed_at=excluded.reviewed_at, notes=excluded.notes
    """, (project_name, stage, reviewed_by, datetime.now().isoformat(), notes))
    conn.commit()
    conn.close()

def get_delivery_owner_reviews(project_name: str) -> Dict[str, Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM delivery_owner_reviews WHERE project_name = ?", (project_name,))
    rows = {r["stage"]: dict(r) for r in cursor.fetchall()}
    conn.close()
    return rows

# --- Content Library (reusable, pre-approved proposal boilerplate) ---

def get_content_library() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM content_library ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def add_content_library_entry(label: str, content: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO content_library (label, content, created_at) VALUES (?, ?, ?)",
        (label, content, datetime.now().isoformat())
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def delete_content_library_entry(entry_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM content_library WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()

# --- Win/Loss Tracking (post-award: what actually happened to the bid) ---

def get_win_loss(project_name: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM win_loss WHERE project_name = ?", (project_name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def set_win_loss(project_name: str, status: str, reason: str = "", decided_by: str = "") -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO win_loss (project_name, status, reason, decided_by, decided_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(project_name) DO UPDATE SET
            status=excluded.status, reason=excluded.reason,
            decided_by=excluded.decided_by, decided_at=excluded.decided_at
    """, (project_name, status, reason, decided_by, now, now))
    conn.commit()
    conn.close()
    return get_win_loss(project_name)

def get_all_win_loss() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM win_loss")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

# --- Estimate vs Actual (post-award: real delivery numbers vs the original bid estimate) ---

def get_project_actuals(project_name: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM project_actuals WHERE project_name = ?", (project_name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def set_project_actuals(project_name: str, actual_total_cost: float, actual_duration_weeks: float,
                         notes: str = "", logged_by: str = "") -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO project_actuals (project_name, actual_total_cost, actual_duration_weeks, notes, logged_by, logged_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(project_name) DO UPDATE SET
            actual_total_cost=excluded.actual_total_cost, actual_duration_weeks=excluded.actual_duration_weeks,
            notes=excluded.notes, logged_by=excluded.logged_by, logged_at=excluded.logged_at
    """, (project_name, actual_total_cost, actual_duration_weeks, notes, logged_by, now))
    conn.commit()
    conn.close()
    return get_project_actuals(project_name)

# --- Cost of Bidding (internal hours/cost spent preparing this bid, win or lose) ---

def get_bid_cost(project_name: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bid_cost_tracking WHERE project_name = ?", (project_name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def set_bid_cost(project_name: str, internal_hours: float, internal_hourly_rate: float = 150,
                  notes: str = "", logged_by: str = "") -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO bid_cost_tracking (project_name, internal_hours, internal_hourly_rate, notes, logged_by, logged_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(project_name) DO UPDATE SET
            internal_hours=excluded.internal_hours, internal_hourly_rate=excluded.internal_hourly_rate,
            notes=excluded.notes, logged_by=excluded.logged_by, logged_at=excluded.logged_at
    """, (project_name, internal_hours, internal_hourly_rate, notes, logged_by, now))
    conn.commit()
    conn.close()
    return get_bid_cost(project_name)

# --- Approval Routing Contacts (department -> notification email) ---

def get_approval_contacts() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM approval_contacts ORDER BY department ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_approval_contact_email(department: str) -> Optional[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM approval_contacts WHERE department = ?", (department,))
    row = cursor.fetchone()
    conn.close()
    return row["email"] if row else None

def set_approval_contact(department: str, email: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO approval_contacts (department, email, updated_at) VALUES (?, ?, ?)
        ON CONFLICT(department) DO UPDATE SET email=excluded.email, updated_at=excluded.updated_at
    """, (department, email, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return get_approval_contacts()

def delete_approval_contact(department: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM approval_contacts WHERE department = ?", (department,))
    conn.commit()
    conn.close()
    return get_approval_contacts()

# --- Proposal Revisions (revise & resend history) ---

def get_proposal_revisions(project_name: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proposal_revisions WHERE project_name = ? ORDER BY version ASC", (project_name,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def add_proposal_revision(project_name: str, subject: str, body: str, sent_in_thread: bool,
                           client_feedback: str = "", message_id: str = None) -> List[Dict[str, Any]]:
    """Logs one send of the proposal as a new version in the history — called every time the proposal
    email is actually sent, so a revise-and-resend cycle is visible instead of silently overwriting.
    Stores THIS send's own Message-ID (not just the most recent one globally) so a client reply to any
    earlier version can still be found later — a client doesn't always reply to the latest resend."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(MAX(version), 0) as v FROM proposal_revisions WHERE project_name = ?", (project_name,))
    next_version = cursor.fetchone()["v"] + 1
    cursor.execute("""
        INSERT INTO proposal_revisions (project_name, version, subject, body, client_feedback, sent_in_thread, message_id, sent_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (project_name, next_version, subject, body, client_feedback, 1 if sent_in_thread else 0, message_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return get_proposal_revisions(project_name)

def get_proposal_message_ids(project_name: str) -> List[str]:
    """All Message-IDs this project's proposal has ever been sent with, most recent first — used to
    search for a client reply to ANY version, since they may reply to an earlier send, not the latest."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT message_id FROM proposal_revisions WHERE project_name = ? AND message_id IS NOT NULL ORDER BY version DESC",
        (project_name,)
    )
    ids = [r["message_id"] for r in cursor.fetchall()]
    conn.close()
    return ids

# --- Contract & Signature Status (manual tracking, not e-signature itself) ---

def get_contract_status(project_name: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contract_status WHERE project_name = ?", (project_name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def set_contract_status(project_name: str, status: str, notes: str = "", updated_by: str = "") -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO contract_status (project_name, status, notes, updated_by, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(project_name) DO UPDATE SET
            status=excluded.status, notes=excluded.notes, updated_by=excluded.updated_by, updated_at=excluded.updated_at
    """, (project_name, status, notes, updated_by, now))
    conn.commit()
    conn.close()
    return get_contract_status(project_name)

# --- Timeline Revisions (schedule disruption log) ---

def get_timeline_revisions(project_name: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM timeline_revisions WHERE project_name = ? ORDER BY id ASC", (project_name,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def add_timeline_revision(project_name: str, trigger_type: str, affected_phase: str, delta_weeks: float,
                           reason: str, cost_impact: float = None, applied_by: str = "") -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO timeline_revisions (project_name, trigger_type, affected_phase, delta_weeks, reason, cost_impact, applied_by, applied_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (project_name, trigger_type, affected_phase, delta_weeks, reason, cost_impact, applied_by, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return get_timeline_revisions(project_name)
