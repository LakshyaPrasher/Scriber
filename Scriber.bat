@echo off
set AIOHTTP_NO_EXTENSIONS=1
cd /d "%~dp0"
rem Prefer the signed CPython runtime used by the installed shortcut; this is the
rem Windows Application Control / Smart App Control compliant launch path.
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "run_desktop.py" %*
) else if exist "dist\Scriber\Scriber.exe" (
    start "" "dist\Scriber\Scriber.exe" %*
) else if exist "Scriber.vbs" (
    start "" wscript "%~dp0Scriber.vbs" %*
) else (
    start "" pythonw "run_desktop.py" %*
)
exit
