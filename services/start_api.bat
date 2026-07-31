@echo off
REM Start Atlas Core API (FastAPI + Uvicorn)
cd /d "%~dp0"
python -m uvicorn atlas_api:app --reload --host 127.0.0.1 --port 8000
