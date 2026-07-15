#!/bin/bash
# Take a screenshot and save it (macOS)
# Usage: screenshot.sh [output_path]
# Example: screenshot.sh screenshot.png

OUTPUT="${1:-screenshot.png}"

# macOS built-in screencapture tool
if [ -f "$OUTPUT" ]; then
    screencapture -x "$OUTPUT"
else
    screencapture -x "$OUTPUT"
fi

if [ $? -eq 0 ]; then
    echo "Screenshot saved: $OUTPUT"
else
    echo "Error: Failed to take screenshot."
    exit 1
fi
