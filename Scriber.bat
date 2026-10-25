@echo off
set AIOHTTP_NO_EXTENSIONS=1
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" run_desktop.py
) else (
    start "" "dist\Scriber\Scriber.exe"
)
