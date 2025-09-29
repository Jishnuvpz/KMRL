@echo off
echo ================================================
echo KMRL Platform Status Check
echo ================================================
echo.

echo Checking Backend (Port 8000)...
powershell -command "try { Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 5 | Select-Object StatusCode, StatusDescription } catch { Write-Host 'Backend not responding' -ForegroundColor Red }"

echo.
echo Checking Frontend (Port 3000)...
powershell -command "try { Invoke-WebRequest -Uri 'http://localhost:3000' -TimeoutSec 5 | Select-Object StatusCode, StatusDescription } catch { Write-Host 'Frontend not responding' -ForegroundColor Red }"

echo.
echo ================================================
echo Access Points:
echo - Frontend: http://localhost:3000
echo - Backend API: http://localhost:8000
echo - API Docs: http://localhost:8000/api/docs
echo - Health Check: http://localhost:8000/health
echo ================================================
pause
