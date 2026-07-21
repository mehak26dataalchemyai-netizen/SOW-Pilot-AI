
@echo off
title SOWPilot AI - FastAPI Backend
echo ==================================================
echo SOWPilot AI - Backend Dev Environment Bootstrapper
echo ==================================================
echo.

:: Move to the backend folder
cd /d "%~dp0backend"

:: Verify Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found on your system path.
    echo Please install Python 3.10+ (and add to environment variables) then run again.
    echo.
    pause
    exit /b
)

:: Check for virtual environment and create if missing
if not exist .venv (
    echo [SYSTEM] Creating virtual environment (.venv)...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b
      )
)

:: Activate the virtual environment
echo [SYSTEM] Activating virtual environment...
call .venv\Scripts\activate.bat

:: Install requirements
echo [SYSTEM] Restoring packages from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Package restoration failed. Check network or python configurations.
    pause
    exit /b
)

:: Prompt Gemini Key Check
echo.
echo [INFO] Ready to launch! Ensure your backend/.env contains a valid GEMINI_API_KEY.
echo.
echo [SYSTEM] Initializing FastAPI dev server with reload...
python main.py

pause
