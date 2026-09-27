# Runs the Assumption Zero analyzer API + dashboard on http://localhost:8010
# The dashboard is served from this same address - just open
# http://localhost:8010 in your browser once this is running.
# Usage (PowerShell):  .\run_analyzer_api.ps1

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
& .\setup.ps1

Write-Host "Starting Assumption Zero analyzer API + dashboard on http://localhost:8010 ..."
Write-Host "Open http://localhost:8010 in your browser once this says 'Application startup complete'."
& .\.venv\Scripts\python.exe -m uvicorn apps.api.main:app --reload --port 8010
