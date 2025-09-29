@echo off
echo KMRL Document Intelligence Platform Setup
echo =========================================

REM Frontend Setup
echo Setting up Frontend (React + Vite)...
if exist "Frontend" (
    cd Frontend
    echo Installing npm dependencies...
    call npm install
    
    echo Copying environment file...
    if not exist ".env" (
        copy ".env.example" ".env"
        echo Please edit Frontend\.env with your API keys
    )
    
    cd ..
) else (
    echo ERROR: Frontend directory not found!
)

REM Backend Setup
echo.
echo Setting up Backend (FastAPI + Python)...
if exist "Backend" (
    cd Backend
    
    echo Creating Python virtual environment...
    if not exist ".venv" (
        python -m venv .venv
    )
    
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
    
    echo Installing Python dependencies...
    pip install -r requirements.txt
    
    echo Copying environment file...
    if not exist ".env" (
        echo Creating default .env file...
        echo DATABASE_URL=sqlite:///./faiss_app.db > .env
        echo SECRET_KEY=your-secret-key-here >> .env
        echo GEMINI_API_KEY=your-gemini-api-key-here >> .env
        echo AWS_ACCESS_KEY_ID=your-aws-key >> .env
        echo AWS_SECRET_ACCESS_KEY=your-aws-secret >> .env
        echo AWS_REGION=us-east-1 >> .env
        echo AWS_S3_BUCKET=your-bucket-name >> .env
        echo Please edit Backend\.env with your actual API keys
    )
    
    cd ..
) else (
    echo ERROR: Backend directory not found!
)

echo.
echo =========================================
echo Setup Complete!
echo.
echo Next steps:
echo 1. Edit Backend\.env with your API keys
echo 2. Edit Frontend\.env with your Gemini API key
echo 3. Run start-dev.bat to start both services
echo.
echo For development:
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:3000
echo - API Docs: http://localhost:8000/api/docs
echo.
pause
