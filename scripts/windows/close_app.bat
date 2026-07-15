REM Close an application by name
REM Usage: close_app.bat <app_name>
REM Example: close_app.bat notepad

@echo off
set APP=%~1
if "%APP%"=="" (
    echo Error: Please provide an application name.
    echo Usage: close_app.bat ^<app_name^>
    exit /b 1
)

taskkill /F /IM "%APP%.exe" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Closed: %APP%
) else (
    echo Warning: Could not close %APP%. It may not be running or the process name differs.
)
