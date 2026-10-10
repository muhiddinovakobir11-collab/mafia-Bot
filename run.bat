@echo off
title Mafia Telegram Bot & Web Admin Panel
echo ========================================================
echo   MAFIA TELEGRAM BOT & WEB ADMIN DASHBOARD
echo   Universal Mafia Bot (@UnvMafiaBot uslubida)
echo ========================================================
echo.
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0main.py"
) else if exist "%USERPROFILE%\.local\bin\uv.exe" (
    "%USERPROFILE%\.local\bin\uv.exe" run python "%~dp0main.py"
) else (
    python "%~dp0main.py"
)
pause
