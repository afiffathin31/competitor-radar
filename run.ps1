# Launcher untuk CompetitorRadar AI Dashboard
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "        MEMULAI COMPETITOR-RADAR AI DASHBOARD             " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

$CurrentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$CurrentDir\backend"

Write-Host "Menjalankan Backend FastAPI di http://127.0.0.1:8000 ..." -ForegroundColor Yellow
Write-Host "Frontend Dashboard aktif dan dapat diakses langsung di http://localhost:8000" -ForegroundColor Green
Write-Host "Tekan Ctrl+C untuk menghentikan server." -ForegroundColor Gray

Start-Process "http://localhost:8000"

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
