#!/bin/bash
# Open an application by name
# Usage: open_app.sh <app_name>
# Example: open_app.sh firefox

APP="$1"

if [ -z "$APP" ]; then
    echo "Error: Please provide an application name."
    echo "Usage: open_app.sh <app_name>"
    exit 1
fi

# Try to launch the application
if command -v "$APP" &> /dev/null; then
    nohup "$APP" &> /dev/null &
    echo "Opened: $APP"
elif command -v gtk-launch &> /dev/null; then
    gtk-launch "$APP" 2>/dev/null &
    echo "Opened: $APP"
else
    echo "Error: Application '$APP' not found."
    exit 1
fi
