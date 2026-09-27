# Runs the flawed demo application (RapidRelief) on http://localhost:8000
# Usage (PowerShell):  .\run_demo_app.ps1

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
& .\setup.ps1

Write-Host "Starting RapidRelief demo app on http://localhost:8000 ..."
& .\.venv\Scripts\python.exe -m uvicorn demo_target.backend.main:app --reload --port 8000
