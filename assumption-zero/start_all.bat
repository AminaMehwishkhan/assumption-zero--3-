@echo off
REM Assumption Zero - one-click Windows launcher.
REM Double-click this file. It installs dependencies once (synchronously,
REM so the two servers never race to install into the same venv), then
REM starts both servers in their own windows and opens the dashboard.
REM No PowerShell execution policy changes needed - this .bat file
REM bypasses that restriction for you by passing -ExecutionPolicy Bypass
REM explicitly, only for the windows it opens (nothing changes
REM system-wide).

cd /d "%~dp0"

echo Setting up (first run may take a minute to install dependencies)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
if errorlevel 1 (
    echo Setup failed - see the message above.
    pause
    exit /b 1
)

echo Starting RapidRelief demo app (http://localhost:8000) in a new window...
start "Assumption Zero - Demo App (port 8000)" powershell -NoExit -ExecutionPolicy Bypass -Command "cd '%~dp0'; .\.venv\Scripts\python.exe -m uvicorn demo_target.backend.main:app --reload --port 8000"

echo Starting analyzer API + dashboard (http://localhost:8010) in a new window...
start "Assumption Zero - Analyzer API (port 8010)" powershell -NoExit -ExecutionPolicy Bypass -Command "cd '%~dp0'; .\.venv\Scripts\python.exe -m uvicorn apps.api.main:app --reload --port 8010"

echo Waiting for servers to start...
timeout /t 5 /nobreak >nul

echo Opening dashboard in your browser...
start http://localhost:8010

echo.
echo Two new windows are now running the demo app and the analyzer API.
echo Keep both windows open. Close this window whenever you like -
echo it does not need to stay open.
pause
