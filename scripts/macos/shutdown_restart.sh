#!/bin/bash
# Shutdown or restart the computer (macOS)
# Usage: shutdown_restart.sh <action>
# Actions: shutdown, restart, logoff, sleep, hibernate
# Example: shutdown_restart.sh restart

ACTION="$1"

if [ -z "$ACTION" ]; then
    echo "Error: Please provide an action."
    echo "Usage: shutdown_restart.sh <action>"
    echo "Actions: shutdown, restart, logoff, sleep, hibernate"
    exit 1
fi

case "$ACTION" in
    shutdown)
        osascript -e 'tell app "System Events" to shut down'
        echo "Shutting down..."
        ;;
    restart)
        osascript -e 'tell app "System Events" to restart'
        echo "Restarting..."
        ;;
    logoff)
        osascript -e 'tell application "System Events" to log out'
        echo "Logging off..."
        ;;
    sleep)
        pmset sleepnow
        echo "Sleeping..."
        ;;
    hibernate)
        # macOS safe sleep (hibernate)
        sudo pmset hibernatemode 25
        sudo pmset sleepnow
        echo "Hibernating..."
        ;;
    *)
        echo "Unknown action: $ACTION"
        echo "Available actions: shutdown, restart, logoff, sleep, hibernate"
        ;;
esac
