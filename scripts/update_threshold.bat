@echo off
setlocal enableextensions
title Update Threshold

REM ============================================================
REM  update_threshold.bat
REM  Updates your Threshold copy to match the latest "main".
REM  If no copy is found anywhere, clones a fresh one to your
REM  Desktop. NOTE: matching main DISCARDS local code changes.
REM ============================================================

set "REPO_URL=https://github.com/AV-ASU/Threshold.git"
set "DEFAULT_DIR=%USERPROFILE%\Desktop\Threshold"

REM Make sure git is available
where git >nul 2>nul
if errorlevel 1 (
  echo.
  echo   Git is not installed or not on your PATH.
  echo   Install it from https://git-scm.com/download/win then retry.
  echo.
  pause
  exit /b 1
)

REM Find an existing git checkout of Threshold
set "REPO="
for %%D in (
  "%~dp0Threshold"
  "%~dp0"
  "%USERPROFILE%\Desktop\Threshold"
  "%USERPROFILE%\Threshold"
  "%USERPROFILE%\Documents\Threshold"
  "%USERPROFILE%\source\repos\Threshold"
) do if not defined REPO if exist "%%~fD\.git" set "REPO=%%~fD"

if not defined REPO (
  echo.
  echo   No existing Threshold copy found.
  echo   Cloning a fresh copy to "%DEFAULT_DIR%" ...
  echo.
  git clone "%REPO_URL%" "%DEFAULT_DIR%"
  if errorlevel 1 ( echo   Clone failed (check your internet). & pause & exit /b 1 )
  echo.
  echo   Done. Threshold is now at "%DEFAULT_DIR%".
  pause
  exit /b 0
)

echo Updating "%REPO%" to match main ...
cd /d "%REPO%"
git fetch origin
if errorlevel 1 ( echo   Fetch failed (check your internet). & pause & exit /b 1 )
git checkout main
git reset --hard origin/main
echo.
echo   Your copy now matches the latest main.
pause
endlocal
