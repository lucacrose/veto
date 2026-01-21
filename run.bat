@echo off

set PYTHON=py
set BACKEND_DIR=backend
set FRONTEND_DIR=frontend
set HOST=0.0.0.0
set PORT=8000

:: Start backend in new window
start "Backend" cmd /k "cd /d %BACKEND_DIR% && echo Starting backend... && %PYTHON% -3.12 -m uvicorn main:app --host %HOST% --port %PORT% --reload"

:: Start frontend in the same window
cd /d %FRONTEND_DIR%
echo Starting frontend...
npm run dev
