@echo off

set BACKEND_DIR=backend
set FRONTEND_DIR=frontend
set HOST=0.0.0.0
set PORT=8000

:: Activate venv
call venv\Scripts\activate.bat

:: Start backend in new window using venv Python
start "Backend" cmd /k "cd /d %BACKEND_DIR% && echo Starting backend... && python -m uvicorn main:app --host %HOST% --port %PORT% --reload"

:: Start frontend in same window
cd /d %FRONTEND_DIR%
echo Starting frontend...
npm run dev
python -m pip install uvicorn