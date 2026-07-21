@echo off
title SOWPilot AI - Vite Frontend
echo ==================================================
echo SOWPilot AI - Frontend Dev Environment Bootstrapper
echo ==================================================
echo.

:: Move to the frontend folder
cd /d "%~dp0frontend"

:: Verify Node.js is installed
node -v >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js or npm was not found on your system path.
    echo Please install Node.js (and add to environment variables) then run again.
    echo.
    pause
    exit /b
)

:: Restore node dependencies if missing
if not exist node_modules (
    echo [SYSTEM] Restoring packages from package.json (npm install)...
    call npm install
    if errorlevel 1 (
        echo [ERROR] Package installation failed. Please check internet connection.
        pause
        exit /b
    )
)

:: Launch development server
echo.
echo [SYSTEM] Bootstrapping Vite React local compiler...
call npm run dev

pause
