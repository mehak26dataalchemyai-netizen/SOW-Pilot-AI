# SOWPilot AI Core Platform

SOWPilot AI is an advanced project planning platform that automatically ingests project requirements (such as Statement of Work files or email attachments), and models deliverables, timelines, resource requirements, budgets, and risks using an AI agent orchestrator.

## 🚀 Features

- **Interactive SaaS Dashboard**: Displays processed projects, active email hooks count, and aggregated costs.
- **AI Processing Panel**: Features dynamic node graph animations showing agent state execution.
- **Real-Time Streaming**: Uses Server-Sent Events (SSE) to stream execution state updates from the backend to the UI.
- **Detailed Project Reports**: Generates breakdowns of cost allocation charts, weekly delivery timelines, and risk assessments.
- **Agent Orchestrator**: Powered by Python, FastAPI, and Google Gemini API.

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18 (TypeScript) with Vite
- **Styling**: Tailwind CSS
- **Visualization**: Recharts, Framer Motion
- **HTTP Client**: Axios

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Web Server**: Uvicorn
- **AI Orchestration**: Parallel DAG / Agent Orchestrator
- **Database**: Local JSON file persistence

---

## 📂 Project Structure

```
Sow Pilot/
├── backend/            # FastAPI Backend
│   ├── .env            # Environment Configuration (Local only)
│   ├── main.py         # Main API Entrypoint
│   ├── orchestrator.py # AI Agent Orchestrator
│   ├── agents.py       # Core Agent Definitions
│   └── data.py         # Data Operations & Utilities
├── frontend/           # React + TypeScript Vite Frontend
│   └── src/            # Source Code
├── .gitignore          # Git Ignored Files and Folders
├── run_backend.bat     # Startup script for Backend (Windows)
└── run_frontend.bat    # Startup script for Frontend (Windows)
```

---

## ⚙️ Getting Started

### 1. Prerequisites
- **Node.js** (v18 or higher)
- **Python** (v3.11 or higher)

### 2. Running the Backend
1. Navigate to the `backend` directory.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Set up your `.env` file with the required API keys:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   # Other configurations...
   ```
4. Run the backend using the root helper script or manually:
   ```bash
   # From root
   run_backend.bat
   ```

### 3. Running the Frontend
1. Navigate to the `frontend` directory.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   # From root
   run_frontend.bat
   ```
