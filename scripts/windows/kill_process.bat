REM Kill a process by name or PID
REM Usage: kill_process.bat <name_or_pid>
REM Example: kill_process.bat notepad.exe
REM Example: kill_process.bat 1234

@echo off
set TARGET=%~1
if "%TARGET%"=="" (
    echo Error: Please provide a process name or PID.
    echo Usage: kill_process.bat ^<name_or_pid^>
    exit /b 1
)

echo %TARGET% | findstr /R "^[0-9][0-9]*$" >nul
if %ERRORLEVEL% EQU 0 (
    taskkill /F /PID %TARGET% >nul 2>&1
    echo Killed process PID: %TARGET%
) else (
    taskkill /F /IM "%TARGET%" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo Killed process: %TARGET%
    ) else (
        echo Warning: Could not kill %TARGET%. Check if the process is running.
    )
)
