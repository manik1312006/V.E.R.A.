REM Open the default web browser with a URL
REM Usage: open_browser.bat [url]
REM Example: open_browser.bat https://google.com

@echo off
set URL=%~1
if "%URL%"=="" (
    set URL=https://www.google.com
)

start "" "%URL%"
echo Opened browser: %URL%
