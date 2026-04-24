#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]}"
while [[ -h "$SCRIPT_PATH" ]]; do
  SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" && pwd)"
  SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
  [[ "$SCRIPT_PATH" != /* ]] && SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_PATH"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" && pwd)"

PYTHON_BIN="${PYTHON_BIN:-$SCRIPT_DIR/.venv/bin/python}"
MENU_URL="${MENU_URL:-https://www.qrcarta.com/restaurant/burjassot/cafeteria-de-farmacia-uv/3616/?type=menu}"
STATE_DIR="${STATE_DIR:-$HOME/.local/state/farmacafe-monitor}"
STATE_FILE="${STATE_FILE:-$STATE_DIR/menu_state.json}"
LAST_JSON="${LAST_JSON:-$STATE_DIR/last_result.json}"
HOOK_SCRIPT="${HOOK_SCRIPT:-$SCRIPT_DIR/farmacafe_on_change.sh}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python executable not found: $PYTHON_BIN" >&2
  exit 1
fi

mkdir -p "$STATE_DIR"
TMP_JSON="$LAST_JSON.tmp"

set +e
"$PYTHON_BIN" "$SCRIPT_DIR/farmacafe_menu_plus.py" \
  --url "$MENU_URL" \
  --json \
  --state-file "$STATE_FILE" \
  --exit-code-on-change 10 > "$TMP_JSON"
status=$?
set -e

mv "$TMP_JSON" "$LAST_JSON"

if [[ $status -eq 0 ]]; then
  echo "No change detected"
  exit 0
fi

if [[ $status -eq 10 ]]; then
  echo "Change detected"
  if [[ -x "$HOOK_SCRIPT" ]]; then
    "$HOOK_SCRIPT" "$LAST_JSON"
  else
    echo "Hook script not executable: $HOOK_SCRIPT" >&2
  fi
  exit 0
fi

echo "Watcher failed with status $status" >&2
exit "$status"
