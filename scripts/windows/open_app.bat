REM Open an application by name
REM Usage: open_app.bat <app_name>
REM Example: open_app.bat notepad

@echo off
set APP=%~1
if "%APP%"=="" (
    echo Error: Please provide an application name.
    echo Usage: open_app.bat ^<app_name^>
    exit /b 1
)

start "" "%APP%"
echo Opened: %APP%
