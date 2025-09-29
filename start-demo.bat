@echo off
echo ================================================
echo KMRL Document Intelligence Platform - Demo
echo ================================================
echo.
echo Starting Backend (FastAPI Demo)...
start "Backend" cmd /k "cd /d Backend && .venv\Scripts\activate && python app/demo_main.py"

echo Waiting for backend to start...
timeout /t 5 /nobreak > nul

echo Starting Frontend (React)...
start "Frontend" cmd /k "cd /d Frontend && npm run dev"

echo.
echo ================================================
echo Services are starting up...
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/api/docs
echo.
echo Demo Login Credentials:
echo - admin@kmrl.co.in / password123 (Admin)
echo - director.ops@kmrl.co.in / password123 (Director)
echo - manager.fin@kmrl.co.in / password123 (Manager)
echo - staff.safety@kmrl.co.in / password123 (Staff)
echo.
echo Press any key to close this launcher...
pause > nul
