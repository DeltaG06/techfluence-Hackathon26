@echo off
echo ============================================================
echo   AuditAI Backend — Starting...
echo ============================================================
cd /d "%~dp0techfluence"
call .venv\Scripts\activate.bat
set PYTHONPATH=%~dp0techfluence
python -m uvicorn auditai_backend.main:app --reload --port 8000
pause
