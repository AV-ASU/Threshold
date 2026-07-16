@echo off
REM ===========================================================================
REM  get_threshold.bat - Download and set up THRESHOLD (first-time install).
REM
REM  Put this file in an empty folder where you want the game to live, then
REM  double-click it. It clones the repo, creates a private virtual
REM  environment, and installs pygame / numpy / scipy into it. Run once.
REM  After this, use start_threshold.bat to play and update_threshold.bat
REM  to pull new versions.
REM ===========================================================================
setlocal
cd /d "%~dp0"

set "REPO_URL=https://github.com/av-asu/threshold.git"
set "GAME_DIR=Threshold"

echo(
echo === THRESHOLD setup ===
echo(

REM --- Check for git ------------------------------------------------------
where git >nul 2>&1
if errorlevel 1 (
    echo [ERROR] git was not found on your PATH.
    echo Install Git for Windows from https://git-scm.com/download/win and
    echo run this file again.
    goto :fail
)

REM --- Check for Python --------------------------------------------------
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] python was not found on your PATH.
    echo Install Python 3 from https://www.python.org/downloads/ ^(tick
    echo "Add python.exe to PATH" in the installer^) and run this file again.
    goto :fail
)

REM --- Clone -------------------------------------------------------------
if exist "%GAME_DIR%\main.py" (
    echo Found an existing copy in "%GAME_DIR%". Skipping clone.
) else (
    echo Cloning THRESHOLD into "%GAME_DIR%" ...
    git clone "%REPO_URL%" "%GAME_DIR%"
    if errorlevel 1 goto :fail
)

cd "%GAME_DIR%"

REM --- Virtual environment + dependencies --------------------------------
if not exist ".venv" (
    echo Creating virtual environment ...
    python -m venv .venv
    if errorlevel 1 goto :fail
)

echo Installing dependencies ^(this can take a minute^) ...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip
call ".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo(
echo === Done. THRESHOLD is installed in "%GAME_DIR%". ===
echo Use start_threshold.bat inside that folder to play.
echo(
pause
exit /b 0

:fail
echo(
echo Setup failed. See the message above.
pause
exit /b 1
