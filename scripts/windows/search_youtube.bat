REM Search YouTube in the default browser
REM Usage: search_youtube.bat <query>
REM Example: search_youtube.bat python tutorial

@echo off
set QUERY=%~1 %~2 %~3 %~4 %~5
if "%QUERY%"=="" (
    echo Error: Please provide a search query.
    echo Usage: search_youtube.bat ^<query^>
    exit /b 1
)

set "QUERY=%QUERY:"=%"
set "QUERY=%QUERY: =+%"

start "" "https://www.youtube.com/results?search_query=%QUERY%"
echo Searching YouTube for: %*
