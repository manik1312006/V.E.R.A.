#!/bin/bash
# Open the default web browser with a URL
# Usage: open_browser.sh [url]
# Example: open_browser.sh https://google.com

URL="${1:-https://www.google.com}"

if command -v xdg-open &> /dev/null; then
    xdg-open "$URL" &>/dev/null &
elif command -v sensible-browser &> /dev/null; then
    sensible-browser "$URL" &>/dev/null &
elif command -v firefox &> /dev/null; then
    firefox "$URL" &>/dev/null &
elif command -v google-chrome &> /dev/null; then
    google-chrome "$URL" &>/dev/null &
else
    echo "Error: No browser found."
    exit 1
fi

echo "Opened browser: $URL"
