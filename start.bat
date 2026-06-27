@echo off
cd /d "%~dp0"

set "NODE_PATH=C:\Users\31167\nodejs\node-v22.16.0-win-x64"

echo ========================================
echo   Parking System - Starting...
echo ========================================
echo.

:: Kill existing
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1

echo [1/2] Starting backend on port 8000...
start "Backend-API" cmd /k "cd /d %~dp0 && .\venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo       Waiting for backend...
timeout /t 4 /nobreak >nul

echo [2/2] Starting frontend on port 5173...
start "Frontend-Vite" cmd /k "cd /d %~dp0frontend && set PATH=%NODE_PATH%;%%PATH%% && npm run dev"

echo       Waiting for frontend...
timeout /t 6 /nobreak >nul

start "" http://localhost:5173

echo.
echo ========================================
echo   System is running!
echo.
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000/docs
echo.
echo   Close the two terminal windows to stop
echo ========================================
echo.
pause
