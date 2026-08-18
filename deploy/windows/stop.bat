@echo off
echo Stopping KyU Campus Connect...
taskkill /F /IM uvicorn.exe 2>nul
echo Server stopped.
