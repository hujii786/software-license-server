@echo off
title Customer Software Server + Live Cloudflare Tunnel
color 0a
echo ======================================================================
echo    Starting Software Server and Exposing to Live Internet (Free)     
echo ======================================================================
echo.

cd /d "%~dp0"

echo [1/2] Starting Local Server on Port 8000...
start "Software Server" cmd /k "python -m uvicorn server.app:app --host 127.0.0.1 --port 8000"

timeout /t 3 >nul

echo [2/2] Connecting to Cloudflare Tunnel for Free Public HTTPS URL...
start "Cloudflare Live Tunnel" cmd /k "cloudflared.exe tunnel --url http://127.0.0.1:8000"

echo.
echo ======================================================================
echo  Server aur Cloudflare dono windows start ho chuki hain!
echo  Cloudflare wali black window mein "https://....trycloudflare.com"
echo  wala link dekhein - wahi aapka live internet URL hai.
echo ======================================================================
echo.
pause
