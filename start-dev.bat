@echo off
echo Starting KMRL Document Intelligence Platform...
echo ================================================

REM Check if both directories exist
if not exist "Frontend" (
    echo ERROR: Frontend directory not found!
    pause
    exit /b 1
)

if not exist "Backend" (
    echo ERROR: Backend directory not found!
    pause
    exit /b 1
)

REM Start Backend
echo Starting Backend (FastAPI)...
start "KMRL Backend" cmd /k "cd /d Backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a moment for backend to start
timeout /t 3 /nobreak > nul

REM Start Frontend
echo Starting Frontend (React + Vite)...
start "KMRL Frontend" cmd /k "cd /d Frontend && npm run dev"

echo.
echo ================================================
echo Both services are starting up...
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/api/docs
echo.
echo Press any key to close this window...
pause > nul
