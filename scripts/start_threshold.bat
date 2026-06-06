@echo off
title Threshold

REM Find the game (your copy is at %USERPROFILE%\Threshold)
set "REPO="
if exist "%USERPROFILE%\Threshold\main.py" set "REPO=%USERPROFILE%\Threshold"
if not defined REPO if exist "%USERPROFILE%\Desktop\Threshold\main.py" set "REPO=%USERPROFILE%\Desktop\Threshold"
if not defined REPO if exist "%USERPROFILE%\Documents\Threshold\main.py" set "REPO=%USERPROFILE%\Documents\Threshold"
if not defined REPO if exist "%~dp0Threshold\main.py" set "REPO=%~dp0Threshold"
if not defined REPO if exist "%~dp0main.py" set "REPO=%~dp0"

if not defined REPO (
  echo Could not find Threshold.
  echo Run update_threshold.bat first to download it.
  pause
  exit /b 1
)

cd /d "%REPO%"

where py >nul 2>nul
if %errorlevel%==0 (set "PY=py") else (set "PY=python")

REM Make sure the game's libraries are installed (first run only)
%PY% -c "import pygame, numpy, scipy" >nul 2>nul
if not %errorlevel%==0 (
  echo Installing required libraries, this only happens once...
  %PY% -m pip install -r requirements.txt
  echo.
)

echo Starting Threshold from %REPO%
echo.
%PY% main.py

echo.
echo Game closed.
pause
