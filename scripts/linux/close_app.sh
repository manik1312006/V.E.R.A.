#!/bin/bash
# Close an application by name
# Usage: close_app.sh <app_name>
# Example: close_app.sh firefox

APP="$1"

if [ -z "$APP" ]; then
    echo "Error: Please provide an application name."
    echo "Usage: close_app.sh <app_name>"
    exit 1
fi

# Kill all processes matching the app name
pkill -f "$APP" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "Closed: $APP"
else
    echo "Warning: Could not close '$APP'. It may not be running."
fi
