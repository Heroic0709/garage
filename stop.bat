@echo off
chcp 65001 >nul
title 关闭停车场管控系统

echo ========================================
echo   正在关闭停车场管控系统...
echo ========================================

:: 关闭后端 (uvicorn) - 树形终结，确保父子进程都关掉
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr LISTENING') do (
    taskkill /PID %%a /T /F >nul 2>&1
    echo [√] 已关闭后端 (端口 8000)
)

:: 关闭前端 (vite/node) - 同样树形终结
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr LISTENING') do (
    taskkill /PID %%a /T /F >nul 2>&1
    echo [√] 已关闭前端 (端口 5173)
)

:: 二次确认
timeout /t 2 /nobreak >nul
netstat -ano | findstr ":8000 " | findstr LISTENING >nul
if %errorlevel% neq 0 (
    echo [√] 后端已确认关闭
) else (
    echo [!] 后端仍运行中，请手动关闭
)

netstat -ano | findstr ":5173 " | findstr LISTENING >nul
if %errorlevel% neq 0 (
    echo [√] 前端已确认关闭
) else (
    echo [!] 前端仍运行中，请手动关闭
)

echo.
echo ========================================
echo   系统已关闭
echo ========================================
pause
