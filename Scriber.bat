@echo off
set AIOHTTP_NO_EXTENSIONS=1
cd /d "%~dp0"
if exist "dist\Scriber\Scriber.exe" (
    start "" "dist\Scriber\Scriber.exe" %*
) else if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" run_desktop.py %*
) else if exist "Scriber.vbs" (
    start "" wscript "%~dp0Scriber.vbs" %*
) else (
    start "" pythonw run_desktop.py %*
)
exit
