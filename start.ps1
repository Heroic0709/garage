Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Parking Management System - Starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# Start backend (use venv python)
Write-Host "[1/2] Starting backend (port 8000)..." -ForegroundColor Yellow
$pythonExe = "$root\venv\Scripts\python.exe"
Start-Process $pythonExe -ArgumentList "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" -WindowStyle Normal
Start-Sleep -Seconds 3

# Start frontend
Write-Host "[2/2] Starting frontend (port 5173)..." -ForegroundColor Yellow
Start-Process npm -ArgumentList "run", "dev" -WorkingDirectory "$root\frontend" -WindowStyle Normal
Start-Sleep -Seconds 3

# Open browser
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  System Ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Open this URL in your browser:" -ForegroundColor White
Write-Host "  http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Close the two opened terminal windows to stop the system." -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to close this window"
