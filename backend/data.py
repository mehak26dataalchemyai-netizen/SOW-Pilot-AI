import os
import json
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects_db.json")

def load_db() -> Dict[str, Any]:
    """Load projects from JSON database file, or initialize a new database."""
    if not os.path.exists(DB_FILE):
        default_db = {
            "projects": [],
            "emails_received_count": 5,  # Base simulated count of received emails
            "processed_email_ids": []    # List of unique email message-ids processed
        }
        save_db(default_db)
        return default_db
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db_data = json.load(f)
            if "processed_email_ids" not in db_data:
                db_data["processed_email_ids"] = []
            return db_data
    except Exception as e:
        print(f"Error loading JSON database, using in-memory default: {e}")
        return {"projects": [], "emails_received_count": 5, "processed_email_ids": []}

def save_db(db_data: Dict[str, Any]) -> None:
    """Save database to JSON file."""
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing to JSON database: {e}")

def is_email_processed(message_id: str) -> bool:
    """Check if the given email Message-ID has already been ingested."""
    db = load_db()
    return message_id in db.get("processed_email_ids", [])

def mark_email_as_processed(message_id: str) -> None:
    """Register the given email Message-ID as processed to avoid duplicates."""
    db = load_db()
    if "processed_email_ids" not in db:
        db["processed_email_ids"] = []
    if message_id not in db["processed_email_ids"]:
        db["processed_email_ids"].append(message_id)
        save_db(db)

def get_all_projects() -> List[Dict[str, Any]]:
    """Retrieve all projects."""
    db = load_db()
    return db.get("projects", [])

def get_latest_project() -> Optional[Dict[str, Any]]:
    """Retrieve the most recently processed project."""
    projects = get_all_projects()
    if not projects:
        return None
    return projects[-1]

def add_project(project: Dict[str, Any]) -> None:
    """Add a new project to the database and increment received email count."""
    db = load_db()
    db["projects"].append(project)
    db["emails_received_count"] = db.get("emails_received_count", 0) + 1
    save_db(db)

def get_dashboard_stats() -> Dict[str, Any]:
    """Compute statistics for dashboard visualization."""
    db = load_db()
    projects = db.get("projects", [])
    emails_received = db.get("emails_received_count", 5)
    
    total_budget = 0
    total_resources = 0
    total_duration_weeks = 0
    projects_processed = len(projects)
    
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
                # Clean currency chars and parse
                clean_str = budget_info.replace("$", "").replace(",", "").strip()
                total_cost = float(clean_str)
            except ValueError:
                total_cost = 0
        total_budget += total_cost
        
        # Resources
        res_info = p.get("resource_plan", {})
        team = res_info.get("recommended_team", [])
        if isinstance(team, list):
            # Sum up member counts if available, otherwise length of list
            for member in team:
                if isinstance(member, dict):
                    total_resources += member.get("count", 1)
                else:
                    total_resources += 1
        elif isinstance(res_info.get("total_resources"), (int, float)):
            total_resources += res_info.get("total_resources")
            
        # Duration
        dur = p.get("project_overview", {}).get("duration", "")
        # Try to parse weeks from string (e.g. "12 weeks" or "3 months")
        weeks = 12 # Default fallback
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
    
    # Calculate total AI agents executed: 6 agents per processed project
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
                "readiness_score": p.get("overall_readiness_score", 0),
                "processed_at": p.get("processed_at", "Just now")
            }
            for p in reversed(projects)
        ]
    }
