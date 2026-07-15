#!/bin/bash
# Take a screenshot and save it
# Usage: screenshot.sh [output_path]
# Example: screenshot.sh screenshot.png

OUTPUT="${1:-screenshot.png}"

if command -v gnome-screenshot &> /dev/null; then
    gnome-screenshot -f "$OUTPUT"
    echo "Screenshot saved: $OUTPUT"
elif command -v scrot &> /dev/null; then
    scrot "$OUTPUT"
    echo "Screenshot saved: $OUTPUT"
elif command -v import &> /dev/null; then
    import -window root "$OUTPUT"
    echo "Screenshot saved: $OUTPUT"
elif command -v xdotool &> /dev/null && command -v xdg &> /dev/null; then
    # Use xdotool + ImageMagick
    DISPLAY=:0 import -window root "$OUTPUT" 2>/dev/null
    echo "Screenshot saved: $OUTPUT"
else
    echo "Error: No screenshot tool found."
    echo "Install one of: gnome-screenshot, scrot, imagemagick"
    exit 1
fi
