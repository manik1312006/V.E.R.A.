#!/bin/bash
# Control system volume using PulseAudio or ALSA
# Usage: volume_control.sh <action> [value]
# Actions: up, down, mute, unmute, set
# Example: volume_control.sh up
# Example: volume_control.sh set 50

ACTION="$1"
VALUE="${2:-5}"

if [ -z "$ACTION" ]; then
    echo "Error: Please provide an action."
    echo "Usage: volume_control.sh <action> [value]"
    echo "Actions: up, down, mute, unmute, set"
    exit 1
fi

if command -v pactl &> /dev/null; then
    # PulseAudio
    case "$ACTION" in
        up)
            pactl set-sink-volume @DEFAULT_SINK@ +${VALUE}%
            echo "Volume increased by ${VALUE}%"
            ;;
        down)
            pactl set-sink-volume @DEFAULT_SINK@ -${VALUE}%
            echo "Volume decreased by ${VALUE}%"
            ;;
        mute)
            pactl set-sink-mute @DEFAULT_SINK@ toggle
            echo "Volume muted (toggled)"
            ;;
        unmute)
            pactl set-sink-mute @DEFAULT_SINK@ 0
            echo "Volume unmuted"
            ;;
        set)
            pactl set-sink-volume @DEFAULT_SINK@ ${VALUE}%
            echo "Volume set to ${VALUE}%"
            ;;
        *)
            echo "Unknown action: $ACTION"
            echo "Available actions: up, down, mute, unmute, set"
            ;;
    esac
elif command -v amixer &> /dev/null; then
    # ALSA fallback
    case "$ACTION" in
        up)
            amixer -q set Master ${VALUE}%+
            echo "Volume increased by ${VALUE}%"
            ;;
        down)
            amixer -q set Master ${VALUE}%-
            echo "Volume decreased by ${VALUE}%"
            ;;
        mute)
            amixer -q set Master toggle
            echo "Volume muted (toggled)"
            ;;
        unmute)
            amixer -q set Master unmute
            echo "Volume unmuted"
            ;;
        set)
            amixer -q set Master ${VALUE}%
            echo "Volume set to ${VALUE}%"
            ;;
        *)
            echo "Unknown action: $ACTION"
            ;;
    esac
else
    echo "Error: No audio control tool found (pactl or amixer)."
    exit 1
fi
