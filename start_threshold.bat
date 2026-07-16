@echo off
REM ===========================================================================
REM  start_threshold.bat - Launch THRESHOLD.
REM
REM  Keep this file in the game's root folder (next to main.py). Double-click
REM  to play. If a .venv virtual environment exists it is used automatically;
REM  otherwise it falls back to the system python.
REM ===========================================================================
setlocal
cd /d "%~dp0"

if not exist "main.py" (
    echo [ERROR] main.py not found next to this batch file.
    echo Make sure start_threshold.bat is in the THRESHOLD game folder.
    pause
    exit /b 1
)

REM --- Pick an interpreter -----------------------------------------------
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"

echo Starting THRESHOLD ...
"%PY%" main.py
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo(
    echo THRESHOLD exited with error code %RC%.
    echo If this mentions a missing module, run update_threshold.bat to
    echo reinstall dependencies.
    pause
)

exit /b %RC%
