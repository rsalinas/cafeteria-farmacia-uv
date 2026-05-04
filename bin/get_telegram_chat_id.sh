#!/usr/bin/env bash
set -euo pipefail

# Helper script to detect Telegram chat ID from bot updates
# Usage: ./bin/get_telegram_chat_id.sh [TOKEN]

TELEGRAM_TOKEN="${1:-${TELEGRAM_TOKEN:-}}"

if [[ -z "$TELEGRAM_TOKEN" ]]; then
  echo "Error: Telegram token required" >&2
  echo "Usage: $0 <token>" >&2
  echo "Or set: export TELEGRAM_TOKEN=..." >&2
  exit 1
fi

echo "Fetching latest updates from Telegram bot..."
echo "(Make sure to send a message to the bot in your channel/group first)" >&2
echo ""

RESPONSE=$(curl -s "https://api.telegram.org/bot$TELEGRAM_TOKEN/getUpdates")

# Try to extract chat ID from different message types
CHAT_ID=$(echo "$RESPONSE" | jq -r '.result[-1].message.chat.id // .result[-1].channel_post.chat.id // empty' 2>/dev/null)

if [[ -z "$CHAT_ID" ]]; then
  echo "❌ No updates found. Make sure to:" >&2
  echo "  1. Add the bot to your channel/group" >&2
  echo "  2. Send a message in that channel/group" >&2
  echo "  3. Run this script again" >&2
  echo "" >&2
  echo "Debug info:" >&2
  echo "$RESPONSE" | jq '.' >&2
  exit 1
fi

echo "✓ Chat ID found:"
echo ""
echo "  TELEGRAM_CHAT_ID=$CHAT_ID"
echo ""
echo "Configure it with:"
echo "  export TELEGRAM_CHAT_ID=$CHAT_ID"
echo ""
echo "Or add to ~/.config/environment.d/farmacafe.conf:"
echo "  TELEGRAM_CHAT_ID=$CHAT_ID"
