# Sri Lakshmi Snacks ERP - Local Server Launcher
Write-Host "=====================================================" -ForegroundColor Yellow
Write-Host "  Sri Lakshmi Snacks - Order-to-Audit ERP (Local Dev) " -ForegroundColor Yellow
Write-Host "=====================================================" -ForegroundColor Yellow

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Check database seed
Write-Host "`n[1/3] Ensuring local SQLite database is seeded..." -ForegroundColor Cyan
$env:PYTHONPATH = "$projectRoot\backend"
& "$projectRoot\backend\.venv\Scripts\python.exe" -m app.seeds.seed

# 2. Launch Backend in new window
Write-Host "[2/3] Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; `$env:PYTHONPATH='backend'; & 'backend\.venv\Scripts\python.exe' -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

# 3. Launch Frontend in new window
Write-Host "[3/3] Starting Vite Frontend on http://localhost:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\frontend'; npm run dev"

Write-Host "`nAll servers launched!" -ForegroundColor Yellow
Write-Host "Open your browser to: http://localhost:5173" -ForegroundColor White
Write-Host "Backend API docs at:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "=====================================================" -ForegroundColor Yellow
