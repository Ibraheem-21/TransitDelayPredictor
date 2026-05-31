# GOPredict launcher
# Usage: right-click > Run with PowerShell, or in a terminal:  .\run.ps1
# First run does setup (venv, pip install, .env, npm install) automatically,
# then starts the backend (http://localhost:8000) and frontend (http://localhost:5173).

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$venv = Join-Path $backend ".venv"

function Write-Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }

# --- Backend setup ---
Write-Step "Checking Python backend"
if (-not (Test-Path $venv)) {
    Write-Host "Creating virtual environment..."
    python -m venv $venv
    & (Join-Path $venv "Scripts\python.exe") -m pip install --upgrade pip
    & (Join-Path $venv "Scripts\pip.exe") install -r (Join-Path $backend "requirements.txt")
} else {
    Write-Host "Virtual environment found, skipping install."
}

$envFile = Join-Path $backend ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "Creating backend\.env from .env.example (add your API keys to enable realtime/weather)."
    Copy-Item (Join-Path $backend ".env.example") $envFile
}

# --- Frontend setup ---
Write-Step "Checking React frontend"
if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "Installing npm dependencies..."
    Push-Location $frontend
    npm install
    Pop-Location
} else {
    Write-Host "node_modules found, skipping install."
}

# --- Launch both servers in separate windows ---
Write-Step "Starting servers"
$backendPython = Join-Path $venv "Scripts\python.exe"

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$backend'; & '$backendPython' -m uvicorn app.main:app --reload"
)

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$frontend'; npm run dev"
)

Write-Host "`nBackend:  http://localhost:8000   (docs at /docs)" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "`nTwo new windows opened (backend + frontend). Close them to stop the servers." -ForegroundColor Yellow
Write-Host "Tip: to load transit data, run in the backend window:  python -m app.scripts.import_gtfs_static" -ForegroundColor DarkGray
