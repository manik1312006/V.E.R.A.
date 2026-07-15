#!/bin/bash
# Open the default web browser with a URL (macOS)
# Usage: open_browser.sh [url]
# Example: open_browser.sh https://google.com

URL="${1:-https://www.google.com}"

open "$URL"
echo "Opened browser: $URL"
