#!/bin/bash
if [ -z "$1" ]; then
    echo "Usage: $0 <path_to_json_file>"
    exit 1
fi
JSON_FILE=$1

if [ ! -f "$JSON_FILE" ]; then
    echo "Error: JSON file not found at $JSON_FILE"
    exit 1
fi

# Load variables via jq
CONFIG_PATH="$HOME/.gemini/antigravity/skills/ai-learning-hub/assets/config.json"
BASE_TOKEN=$(jq -r '.base_token' "$CONFIG_PATH")
FEED_TABLE=$(jq -r '.tables.feed' "$CONFIG_PATH")

echo "[*] Upserting to feed table: $FEED_TABLE in base: $BASE_TOKEN"

# Execute Lark CLI
lark-cli base +record-upsert --base-token "$BASE_TOKEN" --table-id "$FEED_TABLE" --json "$(cat "$JSON_FILE")"
