# Assumption Zero - one-command Windows launcher (PowerShell version).
# Usage:  .\start_all.ps1
# Runs setup once synchronously, then opens two new PowerShell windows
# (one per server) and opens the dashboard in your browser.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "Setting up (first run may take a minute to install dependencies)..."
& .\setup.ps1

Write-Host "Starting RapidRelief demo app (http://localhost:8000) in a new window..."
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", "cd '$PSScriptRoot'; .\.venv\Scripts\python.exe -m uvicorn demo_target.backend.main:app --reload --port 8000"

Write-Host "Starting analyzer API + dashboard (http://localhost:8010) in a new window..."
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", "cd '$PSScriptRoot'; .\.venv\Scripts\python.exe -m uvicorn apps.api.main:app --reload --port 8010"

Write-Host "Waiting for servers to start..."
Start-Sleep -Seconds 5

Write-Host "Opening dashboard in your browser..."
Start-Process "http://localhost:8010"

Write-Host ""
Write-Host "Two new windows are now running the demo app and the analyzer API."
Write-Host "Keep both windows open. This window can be closed."
