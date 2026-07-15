REM List all running processes
REM Usage: list_processes.bat [filter]
REM Example: list_processes.bat chrome

@echo off
set FILTER=%~1
if "%FILTER%"=="" (
    tasklist /FO TABLE
) else (
    tasklist /FI "IMAGENAME eq %FILTER%*" /FO TABLE
)
