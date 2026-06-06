@echo off
setlocal enableextensions
title Threshold

REM ============================================================
REM  start_threshold.bat
REM  Finds your Threshold copy and launches the game.
REM  Looks next to this file first, then common spots.
REM ============================================================

set "REPO="
for %%D in (
  "%~dp0Threshold"
  "%~dp0"
  "%USERPROFILE%\Desktop\Threshold"
  "%USERPROFILE%\Threshold"
  "%USERPROFILE%\Documents\Threshold"
  "%USERPROFILE%\source\repos\Threshold"
) do if not defined REPO if exist "%%~fD\main.py" set "REPO=%%~fD"

if not defined REPO (
  echo.
  echo   Could not find your Threshold copy.
  echo   Run update_threshold.bat first to download it,
  echo   then run this again.
  echo.
  pause
  exit /b 1
)

echo Starting Threshold from "%REPO%"
cd /d "%REPO%"

REM Prefer the Windows Python launcher, fall back to python on PATH
where py >nul 2>nul && (set "PY=py") || (set "PY=python")

%PY% main.py
if errorlevel 1 (
  echo.
  echo   Threshold exited with an error (see above).
  pause
)
endlocal
