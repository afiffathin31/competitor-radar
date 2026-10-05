@echo off
title CompetitorRadar AI Dashboard
echo ==========================================================
echo         MEMULAI COMPETITOR-RADAR AI DASHBOARD
echo ==========================================================
cd /d "%~dp0backend"
start http://localhost:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
