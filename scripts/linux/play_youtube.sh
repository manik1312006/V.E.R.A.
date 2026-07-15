#!/bin/bash
# Play a YouTube video by URL or video ID
# Usage: play_youtube.sh <url_or_id>
# Example: play_youtube.sh https://youtube.com/watch?v=dQw4w9WgXcQ
# Example: play_youtube.sh dQw4w9WgXcQ

INPUT="$1"

if [ -z "$INPUT" ]; then
    echo "Error: Please provide a YouTube URL or video ID."
    echo "Usage: play_youtube.sh <url_or_id>"
    exit 1
fi

# Check if input is a full URL
if echo "$INPUT" | grep -qE "youtube.com|youtu.be"; then
    URL="$INPUT"
else
    URL="https://www.youtube.com/watch?v=$INPUT"
fi

if command -v xdg-open &> /dev/null; then
    xdg-open "$URL" &>/dev/null &
elif command -v open &> /dev/null; then
    open "$URL" &>/dev/null &
else
    echo "Error: No browser opener found."
    exit 1
fi

echo "Playing: $URL"
