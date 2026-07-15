#!/bin/bash
# List all running processes
# Usage: list_processes.sh [filter]
# Example: list_processes.sh chrome

FILTER="$1"

if [ -z "$FILTER" ]; then
    ps aux --sort=-%mem | head -50
else
    ps aux | grep -i "$FILTER" | grep -v grep
fi
