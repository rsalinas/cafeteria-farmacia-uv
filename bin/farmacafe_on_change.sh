#!/usr/bin/env bash
set -euo pipefail

PAYLOAD_FILE="${1:-}"
if [[ -z "$PAYLOAD_FILE" || ! -f "$PAYLOAD_FILE" ]]; then
  echo "Usage: $0 <json_payload_file>" >&2
  exit 1
fi

# Replace this hook body with mail/telegram integration.
echo "[farmacafe_on_change] Change notification triggered"
echo "Payload: $PAYLOAD_FILE"
