@echo off
:: ============================================================
:: Jarvis — One-Click Installer for Windows
:: ============================================================
:: Run this ONCE to set everything up.
:: After this, use run.bat to start Jarvis.
:: ============================================================

title Jarvis Installer — Skyra-Tech
color 0B
echo.
echo  =============================================
echo   J.A.R.V.I.S — Skyra-Tech Installer
echo  =============================================
echo.

:: ── Step 1: Check Python ──────────────────────────────────────
echo [1/6] Checking Python version...
python --version 2>nul
if errorlevel 1 (
    echo.
    echo  ERROR: Python not found!
    echo  Please install Python 3.11+ from https://python.org
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)
echo  Python found!

:: ── Step 2: Create virtual environment ───────────────────────
echo.
echo [2/6] Creating virtual environment...
if exist "venv" (
    echo  Virtual environment already exists — skipping.
) else (
    python -m venv venv
    echo  Virtual environment created!
)

:: ── Step 3: Activate venv ────────────────────────────────────
echo.
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat

:: ── Step 4: Upgrade pip ──────────────────────────────────────
echo.
echo [4/6] Upgrading pip...
python -m pip install --upgrade pip --quiet

:: ── Step 5: Install dependencies ─────────────────────────────
echo.
echo [5/6] Installing dependencies (this takes 2-5 minutes)...
echo  Installing: AI, Voice, Telegram, Audio libraries...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo  ERROR: Installation failed!
    echo  Try running: pip install -r requirements.txt
    pause
    exit /b 1
)
echo  All dependencies installed!

:: ── Step 6: Setup .env ───────────────────────────────────────
echo.
echo [6/6] Setting up configuration...
if not exist ".env" (
    copy .env.example .env
    echo  Created .env file from template.
    echo.
    echo  =========================================
    echo   IMPORTANT: Edit .env with your API keys!
    echo  =========================================
    echo.
    echo  Open .env and fill in:
    echo    GEMINI_API_KEY     = from aistudio.google.com
    echo    TELEGRAM_BOT_TOKEN = from @BotFather on Telegram
    echo    TELEGRAM_ADMIN_CHAT_ID = your Telegram chat ID
    echo.
    notepad .env
) else (
    echo  .env file already exists — skipping.
)

:: ── Done ─────────────────────────────────────────────────────
echo.
echo  =============================================
echo   Installation Complete!
echo  =============================================
echo.
echo  Next steps:
echo  1. Make sure .env has your API keys filled in
echo  2. Double-click run.bat to start Jarvis
echo  3. Say something into your microphone!
echo.
pause
