REM Play a YouTube video by URL or video ID
REM Usage: play_youtube.bat <url_or_id>
REM Example: play_youtube.bat https://youtube.com/watch?v=dQw4w9WgXcQ
REM Example: play_youtube.bat dQw4w9WgXcQ

@echo off
set INPUT=%~1
if "%INPUT%"=="" (
    echo Error: Please provide a YouTube URL or video ID.
    echo Usage: play_youtube.bat ^<url_or_id^>
    exit /b 1
)

echo %INPUT% | findstr /I "youtube.comyoutu.be" >nul
if %ERRORLEVEL% EQU 0 (
    start "" "%INPUT%"
) else (
    start "" "https://www.youtube.com/watch?v=%INPUT%"
)
echo Playing: %INPUT%
