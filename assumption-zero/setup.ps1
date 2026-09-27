# Shared setup: creates .venv and installs dependencies exactly once.
# Called by run_demo_app.ps1, run_analyzer_api.ps1, and start_all.bat so
# nothing ever installs into the same venv concurrently (which corrupts
# the install if two servers try to start at the same time).

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment (.venv)..."
    python -m venv .venv
}

$marker = ".venv\.installed"
$reqHash = (Get-FileHash requirements.txt -Algorithm SHA256).Hash

if (-not (Test-Path $marker) -or (Get-Content $marker -ErrorAction SilentlyContinue) -ne $reqHash) {
    Write-Host "Installing dependencies (first run, or requirements.txt changed)..."
    & .\.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
    & .\.venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
    Set-Content -Path $marker -Value $reqHash
} else {
    Write-Host "Dependencies already installed, skipping."
}
