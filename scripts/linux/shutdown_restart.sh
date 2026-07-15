#!/bin/bash
# Shutdown or restart the computer
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
        echo "Shutting down in 60 seconds. Run 'shutdown -c' to cancel."
        sudo shutdown -h +1
        ;;
    restart)
        echo "Restarting in 60 seconds. Run 'shutdown -c' to cancel."
        sudo shutdown -r +1
        ;;
    logoff)
        case "$XDG_CURRENT_DESKTOP" in
            *GNOME*|*gnome*)
                gnome-session-quit --logout --no-prompt
                ;;
            *KDE*|*kde*)
                qdbus org.kde.ksmserver /KSMServer logout 0 0 0
                ;;
            *)
                pkill -KILL -u "$USER"
                ;;
        esac
        echo "Logging off..."
        ;;
    sleep)
        if command -v systemctl &> /dev/null; then
            sudo systemctl suspend
        else
            echo "Error: systemctl not available for sleep."
            exit 1
        fi
        echo "Sleeping..."
        ;;
    hibernate)
        if command -v systemctl &> /dev/null; then
            sudo systemctl hibernate
        else
            echo "Error: systemctl not available for hibernate."
            exit 1
        fi
        echo "Hibernating..."
        ;;
    *)
        echo "Unknown action: $ACTION"
        echo "Available actions: shutdown, restart, logoff, sleep, hibernate"
        ;;
esac
