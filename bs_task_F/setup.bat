@echo off
setlocal

set "NO_PAUSE="
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"

cd /d "%~dp0"

echo [INFO] SEEG task environment setup
echo [INFO] Working directory: %CD%

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt was not found.
    goto :fail
)

set "PYTHON_CMD="

where py >nul 2>&1
if not errorlevel 1 (
    py -3.10 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 10) else 1)" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3.10"
)

if not defined PYTHON_CMD (
    where python >nul 2>&1
    if not errorlevel 1 (
        python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 10) else 1)" >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=python"
    )
)

if not defined PYTHON_CMD (
    echo [ERROR] Python 3.10 was not found.
    echo [ERROR] Install Python 3.10 from https://www.python.org/downloads/
    echo [ERROR] Enable the Python launcher or add Python to PATH, then run setup.bat again.
    goto :fail
)

echo [INFO] Python command: %PYTHON_CMD%

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Creating .venv...
    %PYTHON_CMD% -m venv ".venv"
    if errorlevel 1 (
        echo [ERROR] Failed to create .venv.
        goto :fail
    )
) else (
    echo [INFO] Reusing existing .venv.
)

".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] The existing .venv does not use Python 3.10.
    echo [ERROR] Remove .venv manually and run setup.bat again.
    goto :fail
)

echo [INFO] Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip.
    goto :fail
)

echo [INFO] Installing requirements...
".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.
    goto :fail
)

echo [INFO] Verifying runtime imports...
".venv\Scripts\python.exe" -c "import psychopy, pandas, openpyxl; from pyjosa.josa import Josa; from labjack import ljm"
if errorlevel 1 (
    echo [ERROR] Runtime import verification failed.
    echo [ERROR] If the LabJack import failed, install the Windows LJM driver and retry.
    goto :fail
)

echo.
echo [SUCCESS] Environment setup is complete.
echo [INFO] Python: %CD%\.venv\Scripts\python.exe
if not defined NO_PAUSE pause
exit /b 0

:fail
echo.
echo [FAILED] Environment setup did not complete.
if not defined NO_PAUSE pause
exit /b 1
