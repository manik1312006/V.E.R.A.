REM Shutdown or restart the computer
REM Usage: shutdown_restart.bat <action>
REM Actions: shutdown, restart, logoff, sleep, hibernate
REM Example: shutdown_restart.bat restart

@echo off
set ACTION=%~1
if "%ACTION%"=="" (
    echo Error: Please provide an action.
    echo Usage: shutdown_restart.bat ^<action^>
    echo Actions: shutdown, restart, logoff, sleep, hibernate
    exit /b 1
)

if /I "%ACTION%"=="shutdown" (
    shutdown /s /t 10 /c "V.E.R.A. is shutting down your computer..."
    echo Shutdown initiated (10 seconds). Run 'shutdown /a' to cancel.
) else if /I "%ACTION%"=="restart" (
    shutdown /r /t 10 /c "V.E.R.A. is restarting your computer..."
    echo Restart initiated (10 seconds). Run 'shutdown /a' to cancel.
) else if /I "%ACTION%"=="logoff" (
    shutdown /l
    echo Logging off...
) else if /I "%ACTION%"=="sleep" (
    rundll32.exe powrprof.dll,SetSuspendState 0,1,0
    echo Sleep initiated.
) else if /I "%ACTION%"=="hibernate" (
    shutdown /h
    echo Hibernating...
) else (
    echo Unknown action: %ACTION%
    echo Available actions: shutdown, restart, logoff, sleep, hibernate
)
