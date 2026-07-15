@echo off
setlocal enabledelayedexpansion

REM ═══════════════════════════════════════════════════════════════════════════
REM  V.E.R.A. Installer — Run this once after cloning/downloading the repo
REM ═══════════════════════════════════════════════════════════════════════════

set "VERA_DIR=%~dp0"
REM Remove trailing backslash
if "%VERA_DIR:~-1%"=="\" set "VERA_DIR=%VERA_DIR:~0,-1%"

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   V.E.R.A. Installer                        ║
echo  ║   Virtual Entity for Real-time Assistance   ║
echo  ╚══════════════════════════════════════════════╝
echo.
echo  Installing from: %VERA_DIR%
echo.

REM ── Step 1: Check Python ──────────────────────────────────────────────────
echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found. Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  Found Python %PYVER%
echo.

REM ── Step 2: Install dependencies ─────────────────────────────────────────
echo [2/4] Installing Python dependencies...
python -m pip install -r "%VERA_DIR%\requirements.txt" --quiet
if errorlevel 1 (
    echo  ERROR: Failed to install dependencies. Check your internet connection.
    pause
    exit /b 1
)
echo  Dependencies installed successfully.
echo.

REM ── Step 3: Set up config ────────────────────────────────────────────────
echo [3/4] Setting up config...
if not exist "%VERA_DIR%\config.yaml" (
    copy "%VERA_DIR%\config.template.yaml" "%VERA_DIR%\config.yaml" >nul
    echo  Created config.yaml from template.
    echo  V.E.R.A. will ask for your API key on first run.
) else (
    echo  config.yaml already exists, skipping.
)
echo.

REM ── Step 4: Add to PATH ───────────────────────────────────────────────────
echo [4/4] Adding V.E.R.A. to your system PATH...
powershell -NoProfile -Command ^
  "$cur = [Environment]::GetEnvironmentVariable('PATH','User'); ^
   if ($cur -notlike '*%VERA_DIR%*') { ^
     [Environment]::SetEnvironmentVariable('PATH', $cur + ';%VERA_DIR%', 'User'); ^
     Write-Host '  Added to PATH successfully.' ^
   } else { ^
     Write-Host '  Already in PATH, skipping.' ^
   }"
echo.

REM ── Done! ─────────────────────────────────────────────────────────────────
echo  ═══════════════════════════════════════════════════
echo   Installation complete!
echo.
echo   Open a NEW terminal window and type:
echo.
echo       vera
echo.
echo   to launch V.E.R.A. from anywhere on your PC.
echo  ═══════════════════════════════════════════════════
echo.
pause
