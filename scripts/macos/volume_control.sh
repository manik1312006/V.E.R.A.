#!/bin/bash
# Control system volume (macOS)
# Usage: volume_control.sh <action> [value]
# Actions: up, down, mute, unmute, set
# Example: volume_control.sh up
# Example: volume_control.sh set 50

ACTION="$1"
VALUE="${2:-10}"

if [ -z "$ACTION" ]; then
    echo "Error: Please provide an action."
    echo "Usage: volume_control.sh <action> [value]"
    echo "Actions: up, down, mute, unmute, set"
    exit 1
fi

case "$ACTION" in
    up)
        osascript -e "set volume output volume ((output volume of (get volume settings)) + $VALUE)"
        echo "Volume increased by $VALUE"
        ;;
    down)
        osascript -e "set volume output volume ((output volume of (get volume settings)) - $VALUE)"
        echo "Volume decreased by $VALUE"
        ;;
    mute)
        osascript -e "set volume output muted true"
        echo "Volume muted."
        ;;
    unmute)
        osascript -e "set volume output muted false"
        echo "Volume unmuted."
        ;;
    set)
        osascript -e "set volume output volume $VALUE"
        echo "Volume set to $VALUE"
        ;;
    *)
        echo "Unknown action: $ACTION"
        echo "Available actions: up, down, mute, unmute, set"
        ;;
esac
