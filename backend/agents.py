import os
import json
import traceback
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environmental variables from .env
load_dotenv(override=True)

# Configure the Groq SDK
api_key = os.getenv("GROQ_API_KEY")
client = None
if api_key and api_key != "YOUR_GROQ_API_KEY_HERE":
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        print("Groq API client configured successfully.")
    except Exception as e:
        print(f"Error configuring Groq client: {e}")
else:
    print("WARNING: Groq API Key not set. Running in simulation mode with mock data.")

def is_api_key_valid() -> bool:
    """Check if a valid Groq API key is present."""
    k = os.getenv("GROQ_API_KEY")
    return k is not None and k != "" and k != "YOUR_GROQ_API_KEY_HERE"

def call_groq_json(prompt: str, system_instruction: str = "") -> Dict[str, Any]:
    """Helper to call Groq with a prompt and force JSON response."""
    global client
    if not is_api_key_valid():
        raise ValueError("Invalid Groq API Key")

    if client is None:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    try:
        # Use llama-3.1-8b-instant, which has high rate-limits and JSON support on Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            temperature=0.2
        )
        content = chat_completion.choices[0].message.content
        
        # Debug logging to file
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "groq_debug.log")
        with open(log_file, "a", encoding="utf-8") as lf:
            lf.write("\n==================================================\n")
            lf.write(f"SYSTEM: {system_instruction}\n")
            lf.write(f"PROMPT: {prompt}\n")
            lf.write(f"RESPONSE: {content}\n")
            lf.write("==================================================\n")
            
        return json.loads(content)
    except Exception as e:
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "groq_debug.log")
        with open(log_file, "a", encoding="utf-8") as lf:
            lf.write("\n==================================================\n")
            lf.write(f"ERROR: {e}\n")
            lf.write(f"PROMPT: {prompt}\n")
            lf.write("==================================================\n")
        print(f"Error calling Groq API: {e}")
        traceback.print_exc()
        raise e

def split_sows_if_multiple(email_text: str) -> List[str]:
    """Uses Groq to separate an email containing multiple SOW descriptions into individual project texts."""
    system_instruction = (
        "You are an expert SOW separator. Read the provided email text and determine if it contains descriptions "
        "for multiple independent projects or statements of work (SOWs).\n"
        "If it describes multiple projects, split the text into a JSON array of strings, where each string contains "
        "the text for one project. If it describes only one project, return a JSON array containing the original text "
        "as the single element. Respond ONLY with a JSON array of strings, for example: [\"project 1 text\", \"project 2 text\", ...]"
    )
    
    prompt = f"Examine this email text and separate into individual SOWs if there are multiple:\n\n{email_text}"
    
    try:
        # If credentials are valid, call Groq
        if is_api_key_valid():
            res = call_groq_json(prompt, system_instruction)
            if isinstance(res, list):
                return res
            elif isinstance(res, dict) and "sows" in res:
                return res["sows"]
            elif isinstance(res, dict) and "projects" in res:
                return res["projects"]
        return [email_text]
    except Exception as e:
        print(f"Error splitting SOWs: {e}")
        return [email_text]

# ==========================================
# AGENT 1: Requirement Extraction Agent
# ==========================================
def extract_requirements(pdf_text: str) -> Dict[str, Any]:
    """Extracts project requirements from SOW/PDF text."""
    system_instruction = (
        "You are an expert project analyst. Read the project Statement of Work (SOW) or requirements document text "
        "and extract key details. You must respond with a JSON object matching this exact structure:\n"
        "{\n"
        "  \"project_name\": \"Name of the project\",\n"
        "  \"client\": \"Client name\",\n"
        "  \"duration\": \"Duration e.g., 3 months\",\n"
        "  \"budget\": \"Budget e.g., $150,000\",\n"
        "  \"tech_stack\": [\"tech1\", \"tech2\", ...],\n"
        "  \"deliverables\": [\"deliverable1\", \"deliverable2\", ...],\n"
        "  \"constraints\": [\"constraint1\", \"constraint2\", ...],\n"
        "  \"dependencies\": [\"dependency1\", \"dependency2\", ...],\n"
        "  \"milestones\": [{\"name\": \"Milestone 1\", \"due_date\": \"Target Date/Week\", \"status\": \"Pending\"}, ...],\n"
        "  \"summary\": \"1-2 sentence executive summary of the requirements\"\n"
        "}"
    )
    
    prompt = f"Please extract project requirements from the following text:\n\n{pdf_text}"
    
    try:
        return call_groq_json(prompt, system_instruction)
    except Exception as e:
        print("Using Requirement Extraction Mock Fallback due to error.")
        # Realistic fallback
        return {
            "project_name": "SOWPilot Core Platform",
            "client": "Apex Enterprise Corp",
            "duration": "16 Weeks",
            "budget": "$240,000",
            "tech_stack": ["React", "FastAPI", "Python", "LangGraph", "PostgreSQL", "Docker", "Tailwind CSS"],
            "deliverables": [
                "Interactive visual dashboard",
                "LangGraph orchestration backend",
                "PDF parser & semantic indexing pipeline",
                "User management & security features",
                "Production-ready deployment scripts"
            ],
            "constraints": ["Must deploy on AWS inside a private VPC", "Strict SOC 2 compliance compliance needed"],
            "dependencies": ["OAuth credentials supplied by client", "Clean access to PDF document repositories"],
            "milestones": [
                {"name": "System Architecture Design", "due_date": "Week 2", "status": "Pending"},
                {"name": "Backend LangGraph Workflow Complete", "due_date": "Week 6", "status": "Pending"},
                {"name": "Frontend Dashboard & SSE Stream Integrations", "due_date": "Week 10", "status": "Pending"},
                {"name": "Beta Deployment & Security Auditing", "due_date": "Week 14", "status": "Pending"},
                {"name": "Production Handover & Launch", "due_date": "Week 16", "status": "Pending"}
            ],
            "summary": "Implement SOWPilot Core Platform, an AI-powered enterprise orchestration system that parses project files and produces visual deliverables."
        }

# ==========================================
# AGENT 2: Resource Allocation Agent
# ==========================================
def allocate_resources(requirements: Dict[str, Any]) -> Dict[str, Any]:
    """Determines team members, competencies, and hiring requirements based on tech stack & scope."""
    system_instruction = (
        "You are an expert Technical Delivery Manager and Resource Planner. Understand the project stack and deliverables, "
        "then estimate the team composition and skill matrix. Respond with a JSON object matching this structure:\n"
        "{\n"
        "  \"required_resources\": [\"Description of necessary role types\"],\n"
        "  \"hiring_needed\": [\"Roles that are not commonly on staff and must be hired/contracted\"],\n"
        "  \"skill_matrix\": [\n"
        "    {\"skill\": \"Technology or skill name\", \"competency_required\": \"Expert/Intermediate/etc\", \"availability\": \"High/Medium/Low\"}\n"
        "  ],\n"
        "  \"recommended_team\": [\n"
        "    {\"role\": \"Role name (e.g. Lead Frontend Developer)\", \"count\": 1, \"key_responsibility\": \"Primary tasks of this person\"}\n"
        "  ]\n"
        "}"
    )
    
    prompt = f"Determine resource allocation for a project with these details:\n\n{json.dumps(requirements, indent=2)}"
    
    try:
        return call_groq_json(prompt, system_instruction)
    except Exception as e:
        print("Using Resource Allocation Mock Fallback due to error.")
        return {
            "required_resources": [
                "Frontend developer fluent in React, Tailwind, and Recharts",
                "Backend engineer with deep FastAPI, LangGraph, and Python LLM orchestration experience",
                "QA Engineer for end-to-end integration and load testing",
                "Part-time DevOps specialist to setup CI/CD and AWS VPC infrastructure"
            ],
            "hiring_needed": [
                "Senior LangGraph / LLM Backend Orchestrator Specialist"
            ],
            "skill_matrix": [
                {"skill": "React / Tailwind", "competency_required": "Advanced", "availability": "High"},
                {"skill": "FastAPI / Python", "competency_required": "Advanced", "availability": "High"},
                {"skill": "LangGraph / AI Agents", "competency_required": "Expert", "availability": "Low"},
                {"skill": "AWS VPC Security", "competency_required": "Intermediate", "availability": "Medium"}
            ],
            "recommended_team": [
                {"role": "Lead Frontend Developer", "count": 1, "key_responsibility": "Build high-performance dashboard and live execution SSE widgets"},
                {"role": "Lead Backend / AI Engineer", "count": 1, "key_responsibility": "Design LangGraph nodes, write Gemini prompts, and connect SSE routes"},
                {"role": "DevOps Engineer", "count": 1, "key_responsibility": "Setup hosting, Docker files, and AWS VPC infrastructure"},
                {"role": "QA Automation Engineer", "count": 1, "key_responsibility": "Conduct API integration testing and browser automation validation"},
                {"role": "Project Manager / BA", "count": 1, "key_responsibility": "Track milestones, facilitate sprint planning, and liaise with Apex Enterprise"}
            ]
        }

# ==========================================
# AGENT 3: Timeline Planning Agent
# ==========================================
def plan_timeline(requirements: Dict[str, Any]) -> Dict[str, Any]:
    """Generates phases, sprints, milestones, and week-by-week delivery details."""
    system_instruction = (
        "You are an expert Project Planner. Using the project deliverables and milestones, "
        "create a detailed phase, sprint, and weekly breakdown. Respond with a JSON object matching this structure:\n"
        "{\n"
        "  \"project_phases\": [\n"
        "    {\"phase_name\": \"Phase name\", \"start_week\": 1, \"end_week\": 4, \"description\": \"Summary of tasks\"}\n"
        "  ],\n"
        "  \"milestones\": [\n"
        "    {\"name\": \"Milestone Name\", \"target_week\": \"Week X\", \"description\": \"Verification criteria\"}\n"
        "  ],\n"
        "  \"sprint_planning\": [\n"
        "    {\"sprint_number\": 1, \"goal\": \"Sprint objective\", \"duration_weeks\": 2, \"tasks\": [\"task1\", \"task2\"]}\n"
        "  ],\n"
        "  \"week_wise_planning\": [\n"
        "    {\"week\": \"Week 1\", \"activities\": [\"activity1\", \"activity2\"], \"deliverables\": [\"deliverable1\"]}\n"
        "  ],\n"
        "  \"estimated_completion\": \"Overall duration summary, e.g. 16 Weeks (4 Months)\"\n"
        "}\n"
        "Optimize phase planning. In particular, any 'Requirements and Design' or 'Discovery and Design' phase must be kept compact and optimal, taking at most 2-3 weeks (e.g., end_week: 2 or 3), regardless of the total project duration, allowing development and testing phases to have the vast majority of duration."
    )
    
    prompt = f"Plan the timeline for a project with these details:\n\n{json.dumps(requirements, indent=2)}"
    
    try:
        return call_groq_json(prompt, system_instruction)
    except Exception as e:
        print("Using Timeline Planning Mock Fallback due to error.")
        return {
            "project_phases": [
                {"phase_name": "Discovery & Design", "start_week": 1, "end_week": 3, "description": "Gather API specifications, design graph schema, write UI wireframes"},
                {"phase_name": "Core Development", "start_week": 4, "end_week": 11, "description": "Implement FastAPI, code the AI orchestrator, create React pages"},
                {"phase_name": "Testing & Integration", "start_week": 12, "end_week": 14, "description": "Run end-to-end integration tests, fix bugs, optimize performance"},
                {"phase_name": "Deployment & Transition", "start_week": 15, "end_week": 16, "description": "Deploy to staging/production, document code, train stakeholders"}
            ],
            "milestones": [
                {"name": "Architecture Sign-off", "target_week": "Week 2", "description": "All data schemas and graph nodes approved"},
                {"name": "API Code Freeze", "target_week": "Week 10", "description": "All main backend and agent routines completed"},
                {"name": "Beta Release", "target_week": "Week 13", "description": "Complete flow working from PDF to report in staging"},
                {"name": "Production Handover", "target_week": "Week 16", "description": "Admin access transferred to client IT staff"}
            ],
            "sprint_planning": [
                {"sprint_number": 1, "goal": "Setup structures and design API", "duration_weeks": 2, "tasks": ["Initialize workspace structures", "Define state interfaces", "Configure Gemini mock/real calls"]},
                {"sprint_number": 2, "goal": "Build requirement parsing graph", "duration_weeks": 2, "tasks": ["Implement PyPDF parsing module", "Write extract agent logic", "Setup SSE stream route"]},
                {"sprint_number": 3, "goal": "Construct parallel execution nodes", "duration_weeks": 2, "tasks": ["Integrate parallel node runners in LangGraph", "Verify state gathering logic"]},
                {"sprint_number": 4, "goal": "Assemble React UI shell and views", "duration_weeks": 2, "tasks": ["Setup Vite tailwind configurations", "Build custom navigation sidebar", "Implement dashboard statistics widget"]},
                {"sprint_number": 5, "goal": "Connect SSE streams and charts", "duration_weeks": 2, "tasks": ["Add AIProcessingPanel state animation hooks", "Integrate Recharts cost visualizations"]},
                {"sprint_number": 6, "goal": "Hardening and Final Deployment", "duration_weeks": 2, "tasks": ["Perform security VPC review", "Final documentation updates", "Trigger production launch"]}
            ],
            "week_wise_planning": [
                {"week": "Week 1", "activities": ["Project kickoff meeting", "Initial database schema modeling", "Review SOW PDFs"], "deliverables": ["Kickoff presentation slide-deck", "Schema diagrams"]},
                {"week": "Week 2", "activities": ["Configure environment variables", "Define LangGraph state nodes", "Confirm system design"], "deliverables": ["Signed architecture spec"]},
                {"week": "Week 3", "activities": ["Code backend mockup and schemas", "Draft Frontend layout wireframes"], "deliverables": ["UI mockups design"]},
                {"week": "Week 4", "activities": ["Write Requirement Extraction Agent prompts", "Integrate PyPDF text parsing"], "deliverables": ["Working PDF parser CLI"]},
                {"week": "Week 5", "activities": ["Code Resource Allocation Agent prompts", "Verify skill matrix schema output"], "deliverables": ["Resource API response"]},
                {"week": "Week 6", "activities": ["Develop Cost Estimation Agent prompts", "Code Risk Analysis Agent prompts"], "deliverables": ["Cost and Risk API responses"]},
                {"week": "Week 7", "activities": ["Write Executive Report synthesis logic", "Construct orchestrator DAG"], "deliverables": ["Draft LangGraph binary"]},
                {"week": "Week 8", "activities": ["Configure Server-Sent Events (SSE) stream endpoints", "Create React dashboard base"], "deliverables": ["API SSE endpoint"]},
                {"week": "Week 9", "activities": ["Build React Sidebar & routing structures", "Integrate state contexts"], "deliverables": ["Functional UI navigation"]},
                {"week": "Week 10", "activities": ["Implement AIProcessingPanel nodes animation", "Format status triggers"], "deliverables": ["Live animation flow"]},
                {"week": "Week 11", "activities": ["Connect Recharts charts in ProjectDetails view", "Map data bindings"], "deliverables": ["Operational visual charts"]},
                {"week": "Week 12", "activities": ["Run complete system local dry-runs", "Fix edge UI overflow errors"], "deliverables": ["Stability validation report"]},
                {"week": "Week 13", "activities": ["Run API unit tests", "Test Gemini extraction accuracy rates"], "deliverables": ["Lighthouse & test output logs"]},
                {"week": "Week 14", "activities": ["VPC networking configuration", "Audit container deployment logs"], "deliverables": ["VPC staging deployment"]},
                {"week": "Week 15", "activities": ["Collect final user feedback", "Draft administrative hand-off guides"], "deliverables": ["User manual documentation"]},
                {"week": "Week 16", "activities": ["Perform live staging dry-run", "Transfer AWS account access"], "deliverables": ["Production launch sign-off"]}
            ],
            "estimated_completion": "16 Weeks"
        }

# ==========================================
# AGENT 4: Cost Estimation Agent
# ==========================================
def estimate_costs(requirements: Dict[str, Any]) -> Dict[str, Any]:
    """Estimates project costs: development, cloud, infrastructure, testing, support, buffer, total."""
    system_instruction = (
        "You are an expert Cost Estimator and IT Accountant. Based on the duration, team requirements, and scope, "
        "calculate individual cost items. Make sure your values are numbers (integers or floats). Respond with a JSON object matching this structure:\n"
        "{\n"
        "  \"development_cost\": 150000,\n"
        "  \"cloud_cost\": 12000,\n"
        "  \"infrastructure_cost\": 8000,\n"
        "  \"testing_cost\": 15000,\n"
        "  \"support_cost\": 10000,\n"
        "  \"buffer_cost\": 20000,\n"
        "  \"total_cost\": 215000\n"
        "}"
    )
    
    prompt = f"Estimate the cost details for this project:\n\n{json.dumps(requirements, indent=2)}"
    
    try:
        return call_groq_json(prompt, system_instruction)
    except Exception as e:
        print("Using Cost Estimation Mock Fallback due to error.")
        return {
            "development_cost": 172000,
            "cloud_cost": 14000,
            "infrastructure_cost": 9000,
            "testing_cost": 16000,
            "support_cost": 12000,
            "buffer_cost": 17000,
            "total_cost": 240000
        }

# ==========================================
# AGENT 5: Risk Analysis Agent
# ==========================================
def analyze_risks(requirements: Dict[str, Any]) -> Dict[str, Any]:
    """Predicts hiring, timeline, technology, budget, compliance, and dependency risks."""
    system_instruction = (
        "You are an expert Project Risk Assessor. Evaluate the risks associated with this SOW. "
        "Respond with a JSON object containing a list of risk items. Each risk item must contain "
        "category (e.g. Hiring Risk, Timeline Risk, Technology Risk, Budget Risk, Compliance Risk, Third Party Dependency Risk), "
        "severity (Low/Medium/High), probability (Low/Medium/High), risk_name, and mitigation. Respond with this structure:\n"
        "{\n"
        "  \"risks\": [\n"
        "    {\n"
        "      \"category\": \"Technology Risk\",\n"
        "      \"risk_name\": \"LangGraph Orchestrator Complexity\",\n"
        "      \"severity\": \"Medium\",\n"
        "      \"probability\": \"Medium\",\n"
        "      \"mitigation\": \"Establish small mock node graph spikes early in the development lifecycle.\"\n"
        "    }\n"
        "  ]\n"
        "}"
    )
    
    prompt = f"Analyze risks for this project:\n\n{json.dumps(requirements, indent=2)}"
    
    try:
        return call_groq_json(prompt, system_instruction)
    except Exception as e:
        print("Using Risk Analysis Mock Fallback due to error.")
        return {
            "risks": [
                {
                    "category": "Hiring Risk",
                    "risk_name": "LangGraph Specialist Availability",
                    "severity": "High",
                    "probability": "Medium",
                    "mitigation": "Initiate developer search immediately or allocate an experienced in-house senior backend engineer for upskilling."
                },
                {
                    "category": "Timeline Risk",
                    "risk_name": "VPC Network Access Delays",
                    "severity": "Medium",
                    "probability": "High",
                    "mitigation": "Include VPC design approval in Week 2 milestone, requesting credentials from Apex Enterprise immediately at kickoff."
                },
                {
                    "category": "Technology Risk",
                    "risk_name": "Gemini API Rate Limiting",
                    "severity": "Low",
                    "probability": "Medium",
                    "mitigation": "Implement local response caching and rate limit retries in the agents.py SDK API caller."
                },
                {
                    "category": "Budget Risk",
                    "risk_name": "Scope Creep on Visual Dashboard",
                    "severity": "Medium",
                    "probability": "Low",
                    "mitigation": "Hold strict sprint review demos with Apex PM to confirm alignment on pre-existing specs before editing dashboard components."
                },
                {
                    "category": "Compliance Risk",
                    "risk_name": "SOC 2 Audit Delays",
                    "severity": "Medium",
                    "probability": "Low",
                    "mitigation": "Use pre-audited secure cloud templates and track compliance rules as part of continuous integration pipelines."
                },
                {
                    "category": "Third Party Dependency Risk",
                    "risk_name": "PDF Formatting Variance",
                    "severity": "High",
                    "probability": "Medium",
                    "mitigation": "Build robust fallback parsing models and define a clean standardized text interface before loading PDF contents into LLM prompts."
                }
            ]
        }

# ==========================================
# AGENT 6: Executive Report Agent
# ==========================================
def generate_executive_report(
    requirements: Dict[str, Any],
    resources: Dict[str, Any],
    timeline: Dict[str, Any],
    costs: Dict[str, Any],
    risks: Dict[str, Any]
) -> Dict[str, Any]:
    """Combines all previous agent outputs into a unified comprehensive executive delivery report."""
    system_instruction = (
        "You are an expert Project Delivery Executive. Synthesize all the individual reports from the extraction, "
        "resource planning, timeline planning, cost estimation, and risk analysis teams into a final, unified executive report. "
        "Make sure to assign an 'overall_readiness_score' between 0 and 100 based on the risks and plan coverage. "
        "Respond with a JSON object matching this structure:\n"
        "{\n"
        "  \"executive_summary\": \"Consolidated high-level project summary\",\n"
        "  \"project_overview\": {\n"
        "    \"project_name\": \"Project Name\",\n"
        "    \"client\": \"Client Name\",\n"
        "    \"duration\": \"E.g. 16 Weeks\",\n"
        "    \"budget\": \"Total cost string\"\n"
        "  },\n"
        "  \"technology_summary\": {\n"
        "    \"stack\": [\"tech1\", \"tech2\"],\n"
        "    \"deliverables\": [\"deliverable1\", \"deliverable2\"],\n"
        "    \"recommendation\": \"Advice on technical selection, tooling, and environment setup\"\n"
        "  },\n"
        "  \"resource_plan\": {\n"
        "    \"team_summary\": \"Short overview of the recommended resource plan\",\n"
        "    \"recommended_team\": [{\"role\": \"Role name\", \"count\": 1, \"key_responsibility\": \"tasks\"}],\n"
        "    \"total_resources\": 5\n"
        "  },\n"
        "  \"timeline\": {\n"
        "    \"phases\": [{\"phase_name\": \"Phase\", \"start_week\": 1, \"end_week\": 4, \"description\": \"details\"}],\n"
        "    \"sprint_planning\": [{\"sprint_number\": 1, \"goal\": \"Sprint objective\", \"duration_weeks\": 2, \"tasks\": [\"task1\", \"task2\"]}],\n"
        "    \"week_wise_planning\": [{\"week\": \"Week 1\", \"activities\": [\"activity1\", \"activity2\"], \"deliverables\": [\"deliverable1\"]}],\n"
        "    \"estimated_completion\": \"16 Weeks\"\n"
        "  },\n"
        "  \"budget\": {\n"
        "    \"breakdown\": {\n"
        "      \"development_cost\": 150000,\n"
        "      \"cloud_cost\": 12000,\n"
        "      \"infrastructure_cost\": 8000,\n"
        "      \"testing_cost\": 15000,\n"
        "      \"support_cost\": 10000,\n"
        "      \"buffer_cost\": 20000\n"
        "    },\n"
        "    \"total_cost\": 215000\n"
        "  },\n"
        "  \"risks\": [\n"
        "    {\"risk_name\": \"Risk\", \"severity\": \"High/Medium/Low\", \"probability\": \"High/Medium/Low\", \"mitigation\": \"mitigation details\"}\n"
        "  ],\n"
        "  \"recommendations\": [\"recommendation 1\", \"recommendation 2\"],\n"
        "  \"overall_readiness_score\": 85\n"
        "}"
    )
    
    combined_inputs = {
        "requirements": requirements,
        "resource_allocation": resources,
        "timeline_plan": timeline,
        "cost_estimation": costs,
        "risk_analysis": risks
    }
    
    prompt = f"Synthesize these delivery components into the final executive JSON report:\n\n{json.dumps(combined_inputs, indent=2)}"
    
    try:
        return call_groq_json(prompt, system_instruction)
    except Exception as e:
        print("Using Executive Report Synthesis Mock Fallback due to error.")
        # Make sure values align
        total_res = sum([x.get("count", 1) for x in resources.get("recommended_team", [])])
        return {
            "executive_summary": "SOWPilot Core Platform is highly viable for Apex Enterprise Corp. With a structured 16-week timeline, an allocated 5-person technical delivery team, and a total estimated cost of $240,000, the project displays strong organizational alignment. Mitigation plans for LangGraph developer sourcing and VPC credentials need immediate activation.",
            "project_overview": {
                "project_name": requirements.get("project_name", "SOWPilot Core Platform"),
                "client": requirements.get("client", "Apex Enterprise Corp"),
                "duration": requirements.get("duration", "16 Weeks"),
                "budget": f"${costs.get('total_cost', 240000):,}"
            },
            "technology_summary": {
                "stack": requirements.get("tech_stack", ["React", "FastAPI", "Python", "LangGraph", "Docker", "Tailwind CSS"]),
                "deliverables": requirements.get("deliverables", []),
                "recommendation": "Use Python 3.11 with FastAPI for the backend. Standardize on React 18, Vite, and Tailwind CSS v3 for frontend dashboards. Ensure AWS Elastic Container Service (ECS) and RDS PostgreSQL are deployed within a secure subnet."
            },
            "resource_plan": {
                "team_summary": "Establish a balanced engineering crew comprising 1 Lead Frontend, 1 Lead Backend/AI, 1 DevOps, 1 QA Engineer, led by a hybrid Project Manager/Business Analyst.",
                "recommended_team": resources.get("recommended_team", []),
                "total_resources": total_res
            },
            "timeline": {
                "phases": timeline.get("project_phases", []),
                "sprint_planning": timeline.get("sprint_planning", []),
                "week_wise_planning": timeline.get("week_wise_planning", []),
                "estimated_completion": timeline.get("estimated_completion", "16 Weeks")
            },
            "budget": {
                "breakdown": {
                    "development_cost": costs.get("development_cost", 172000),
                    "cloud_cost": costs.get("cloud_cost", 14000),
                    "infrastructure_cost": costs.get("infrastructure_cost", 9000),
                    "testing_cost": costs.get("testing_cost", 16000),
                    "support_cost": costs.get("support_cost", 12000),
                    "buffer_cost": costs.get("buffer_cost", 17000)
                },
                "total_cost": costs.get("total_cost", 240000)
            },
            "risks": risks.get("risks", []),
            "recommendations": [
                "Establish LangGraph backend scaffolding in Week 1 to validate event streaming.",
                "Request AWS VPC access keys from Apex Enterprise IT during kickoff to prevent Week 2 deployment blocks.",
                "Implement robust caching for Gemini 2.5 Flash API calls to keep processing costs low."
            ],
            "overall_readiness_score": 82
        }
