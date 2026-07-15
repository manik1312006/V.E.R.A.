REM Control system volume
REM Usage: volume_control.bat <action> [value]
REM Actions: up, down, mute, unmute, set
REM Example: volume_control.bat up
REM Example: volume_control.bat set 50

@echo off
set ACTION=%~1
if "%ACTION%"=="" (
    echo Error: Please provide an action.
    echo Usage: volume_control.bat ^<action^> [value]
    echo Actions: up, down, mute, unmute, set
    exit /b 1
)

powershell -Command "
Add-Type -TypeDefinition 'using System.Runtime.InteropServices; public class Audio { [DllImport(\"user32.dll\")] public static extern IntPtr SendMessageW(IntPtr hWnd, int Msg, IntPtr wParam, IntPtr lParam); }'
" 2>nul

if /I "%ACTION%"=="mute" (
    powershell -Command "$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]173)"
    echo Volume muted.
) else if /I "%ACTION%"=="unmute" (
    powershell -Command "$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]173)"
    echo Volume unmuted (toggled).
) else if /I "%ACTION%"=="up" (
    powershell -Command "$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]175)"
    echo Volume increased.
) else if /I "%ACTION%"=="down" (
    powershell -Command "$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]174)"
    echo Volume decreased.
) else if /I "%ACTION%"=="set" (
    echo Note: Precise volume setting requires nircmd or third-party tool.
    echo Use 'up' and 'down' to adjust volume incrementally.
) else (
    echo Unknown action: %ACTION%
    echo Available actions: up, down, mute, unmute, set
)
