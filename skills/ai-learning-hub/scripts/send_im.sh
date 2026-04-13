#!/bin/bash
if [ -z "$1" ]; then
    echo "Usage: $0 <path_to_markdown_file>"
    exit 1
fi
MD_FILE=$1

if [ ! -f "$MD_FILE" ]; then
    echo "Error: Markdown file not found at $MD_FILE"
    exit 1
fi

# Load variables via jq
CONFIG_PATH="$HOME/.gemini/antigravity/skills/ai-learning-hub/assets/config.json"
USER_ID=$(jq -r '.user_open_id' "$CONFIG_PATH")

echo "[*] Sending Markdown report to user: $USER_ID"

# Execute Lark CLI
lark-cli im +messages-send --as bot --user-id "$USER_ID" --markdown "$(cat "$MD_FILE")"
