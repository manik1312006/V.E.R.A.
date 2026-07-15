#!/bin/bash
# Open an application by name (macOS)
# Usage: open_app.sh <app_name>
# Example: open_app.sh Safari
# Example: open_app.sh "Google Chrome"

APP="$1"

if [ -z "$APP" ]; then
    echo "Error: Please provide an application name."
    echo "Usage: open_app.sh <app_name>"
    exit 1
fi

# Try using 'open -a' for macOS applications
open -a "$APP" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Opened: $APP"
else
    # Fallback: try as a command-line tool
    if command -v "$APP" &> /dev/null; then
        nohup "$APP" &> /dev/null &
        echo "Opened: $APP"
    else
        echo "Error: Application '$APP' not found."
        exit 1
    fi
fi
