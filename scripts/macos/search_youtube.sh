#!/bin/bash
# Search YouTube in the default browser (macOS)
# Usage: search_youtube.sh <query>
# Example: search_youtube.sh python tutorial

QUERY="$*"

if [ -z "$QUERY" ]; then
    echo "Error: Please provide a search query."
    echo "Usage: search_youtube.sh <query>"
    exit 1
fi

# URL-encode the query
ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote_plus('''$QUERY'''))" 2>/dev/null || echo "$QUERY" | tr ' ' '+')

open "https://www.youtube.com/results?search_query=$ENCODED"
echo "Searching YouTube for: $QUERY"
