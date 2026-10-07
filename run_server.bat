@echo off
title Personal Customer Software Server Hub
color 0b
echo ============================================================
echo      Starting Customer Software Hub & Licensing Server      
echo ============================================================
echo.

cd /d "%~dp0"
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload

pause
