@echo off
setlocal

set "NO_PAUSE="
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] The experiment environment is not installed.
    echo [ERROR] Run setup.bat first.
    if not defined NO_PAUSE pause
    exit /b 1
)

echo [INFO] Starting the SEEG task...
".venv\Scripts\python.exe" "main.py"
set "TASK_EXIT_CODE=%ERRORLEVEL%"

if not "%TASK_EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] The experiment exited with code %TASK_EXIT_CODE%.
)

if not defined NO_PAUSE pause
exit /b %TASK_EXIT_CODE%
