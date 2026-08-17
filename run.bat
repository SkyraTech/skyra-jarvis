@echo off
:: ============================================================
:: Jarvis — Start Script for Windows
:: ============================================================
:: Double-click this to start Jarvis.
:: ============================================================

title J.A.R.V.I.S — Skyra-Tech
color 0B

echo.
echo  =============================================
echo   Starting J.A.R.V.I.S — Skyra-Tech
echo  =============================================
echo.

:: Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo  ERROR: Virtual environment not found!
    echo  Please run install.bat first.
    echo.
    pause
    exit /b 1
)

:: Check if .env exists
if not exist ".env" (
    echo  ERROR: .env file not found!
    echo  Please run install.bat first and fill in your API keys.
    echo.
    pause
    exit /b 1
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Start Jarvis
echo  Launching Jarvis...
echo  Press Ctrl+C to stop.
echo.
python main.py %*

echo.
echo  Jarvis stopped.
pause
