#!/bin/bash
# List all running processes (macOS)
# Usage: list_processes.sh [filter]
# Example: list_processes.sh Safari

FILTER="$1"

if [ -z "$FILTER" ]; then
    ps aux --sort=-%mem | head -50
else
    ps aux | grep -i "$FILTER" | grep -v grep
fi
