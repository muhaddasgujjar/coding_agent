@echo off
echo Cleaning up old background instances...
netstat -ano | findstr :8000 > nul
if %errorlevel% equ 0 (
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /f /pid %%a > nul 2>&1
)

echo Starting FastAPI Backend...
start cmd /k "cd server & .venv\Scripts\python.exe main.py"

echo Starting Vite React Frontend...
cd client
npm run dev
