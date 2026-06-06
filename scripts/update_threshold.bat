@echo off
title Update Threshold

where git >nul 2>nul
if not %errorlevel%==0 (
  echo Git is not installed or not on PATH.
  echo Get it from https://git-scm.com/download/win then try again.
  pause
  exit /b 1
)

REM Find an existing copy
set "REPO="
if exist "%USERPROFILE%\Threshold\.git" set "REPO=%USERPROFILE%\Threshold"
if not defined REPO if exist "%USERPROFILE%\Desktop\Threshold\.git" set "REPO=%USERPROFILE%\Desktop\Threshold"
if not defined REPO if exist "%USERPROFILE%\Documents\Threshold\.git" set "REPO=%USERPROFILE%\Documents\Threshold"
if not defined REPO if exist "%~dp0Threshold\.git" set "REPO=%~dp0Threshold"

if not defined REPO (
  echo No Threshold copy found. Cloning a fresh one...
  git clone https://github.com/AV-ASU/Threshold.git "%USERPROFILE%\Threshold"
  echo.
  echo Done. Threshold is now at %USERPROFILE%\Threshold
  pause
  exit /b 0
)

cd /d "%REPO%"
echo Updating %REPO% to match main...
echo.
git fetch origin
git checkout main
git reset --hard origin/main
echo.
echo Done. Your copy now matches main.
pause
