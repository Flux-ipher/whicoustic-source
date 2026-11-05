@echo off
echo Starting Whicoustic Development Environment...
echo.

REM Check if Docker is running
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker is not running or not installed. Please start Docker Desktop.
    pause
    exit /b 1
)

echo Starting services with Docker Compose...
docker-compose up -d postgres redis

echo Waiting for services to be ready...
timeout /t 10

echo Starting Backend (FastAPI)...
start cmd /k "cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 5

echo Starting Frontend (Next.js)...
start cmd /k "cd frontend && npm run dev"

echo.
echo Development environment started!
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to stop all services...
pause

echo Stopping services...
docker-compose down
taskkill /f /im node.exe 2>nul
taskkill /f /im python.exe 2>nul

echo Development environment stopped.
pause
