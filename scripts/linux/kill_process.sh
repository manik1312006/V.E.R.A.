#!/bin/bash
# Kill a process by name or PID
# Usage: kill_process.sh <name_or_pid>
# Example: kill_process.sh firefox
# Example: kill_process.sh 1234

TARGET="$1"

if [ -z "$TARGET" ]; then
    echo "Error: Please provide a process name or PID."
    echo "Usage: kill_process.sh <name_or_pid>"
    exit 1
fi

# Check if target is a number (PID)
if echo "$TARGET" | grep -qE "^[0-9]+$"; then
    kill -9 "$TARGET" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Killed process PID: $TARGET"
    else
        echo "Warning: Could not kill PID $TARGET. It may not exist."
    fi
else
    pkill -9 -f "$TARGET" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Killed process: $TARGET"
    else
        echo "Warning: Could not kill '$TARGET'. It may not be running."
    fi
fi
