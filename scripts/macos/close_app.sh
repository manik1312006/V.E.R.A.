#!/bin/bash
# Close an application by name (macOS)
# Usage: close_app.sh <app_name>
# Example: close_app.sh Safari

APP="$1"

if [ -z "$APP" ]; then
    echo "Error: Please provide an application name."
    echo "Usage: close_app.sh <app_name>"
    exit 1
fi

# Try using osascript for proper macOS app closing
osascript -e "tell application \"$APP\" to quit" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Closed: $APP"
else
    # Fallback: kill by process name
    pkill -f "$APP" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Closed: $APP"
    else
        echo "Warning: Could not close '$APP'. It may not be running."
    fi
fi
