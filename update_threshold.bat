@echo off
REM ===========================================================================
REM  update_threshold.bat - Pull the latest THRESHOLD and refresh dependencies.
REM
REM  Keep this file in the game's root folder (next to main.py). Double-click
REM  to fetch the newest version from GitHub and reinstall any changed
REM  dependencies. Your local save (~\.threshold) is untouched.
REM ===========================================================================
setlocal
cd /d "%~dp0"

if not exist ".git" (
    echo [ERROR] This folder is not a git checkout, so it cannot self-update.
    echo Re-download using get_threshold.bat instead.
    pause
    exit /b 1
)

where git >nul 2>&1
if errorlevel 1 (
    echo [ERROR] git was not found on your PATH.
    echo Install Git for Windows from https://git-scm.com/download/win.
    pause
    exit /b 1
)

echo === Updating THRESHOLD ===
echo(

REM --- Warn about local edits so a pull cannot fail silently --------------
git diff --quiet
if errorlevel 1 (
    echo [WARN] You have local changes to game files. They may block the update.
    echo Press Ctrl+C to cancel, or any key to try stashing them and continue.
    pause >nul
    git stash push -m "update_threshold auto-stash"
)

echo Pulling latest changes ...
git pull --ff-only
if errorlevel 1 (
    echo(
    echo [ERROR] Update failed. You may need to resolve this manually.
    pause
    exit /b 1
)

REM --- Refresh dependencies ----------------------------------------------
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"

echo Refreshing dependencies ...
"%PY%" -m pip install -r requirements.txt

echo(
echo === THRESHOLD is up to date. Use start_threshold.bat to play. ===
pause
exit /b 0
