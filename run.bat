@echo off
title ContagionMap Pipeline
setlocal

set PYTHON=C:\msys64\ucrt64\bin\python3.exe

echo ==================================================
echo   ContagionMap — Launcher
echo ==================================================

:: Check .env exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Please copy .env.example to .env and fill in your MySQL credentials.
    pause
    exit /b 1
)

:: Step 0 — Setup database (creates DB + schema if needed)
echo.
echo [Step 0] Setting up database...
%PYTHON% setup_db.py
if errorlevel 1 (
    echo [ERROR] Database setup failed. Check your .env credentials.
    pause
    exit /b 1
)

:: Step 1 — Run full pipeline
echo.
echo [Step 1] Running full pipeline...
%PYTHON% pipeline\run_pipeline.py
if errorlevel 1 (
    echo [ERROR] Pipeline failed. See output above.
    pause
    exit /b 1
)

echo.
echo ==================================================
echo   Done! Check the exports\ folder for output CSVs.
echo ==================================================
pause
