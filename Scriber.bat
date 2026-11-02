@echo off
set AIOHTTP_NO_EXTENSIONS=1
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" run_desktop.py %*
) else if exist "dist\Scriber\Scriber.exe" (
    start "" "dist\Scriber\Scriber.exe" %*
) else (
    start "" python run_desktop.py %*
)
