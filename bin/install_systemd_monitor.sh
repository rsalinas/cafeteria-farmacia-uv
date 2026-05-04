#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]}"
while [[ -h "$SCRIPT_PATH" ]]; do
  SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" && pwd)"
  SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
  [[ "$SCRIPT_PATH" != /* ]] && SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_PATH"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" && pwd)"
REPO_DIR="$(cd -P "$SCRIPT_DIR/.." && pwd)"

USER_SYSTEMD_DIR="${HOME}/.config/systemd/user"
SERVICE_TEMPLATE="$REPO_DIR/systemd/farmacafe-monitor.service.template"
TIMER_TEMPLATE="$REPO_DIR/systemd/farmacafe-monitor.timer.template"
SERVICE_FILE="$USER_SYSTEMD_DIR/farmacafe-monitor.service"
TIMER_FILE="$USER_SYSTEMD_DIR/farmacafe-monitor.timer"

if [[ ! -x "$REPO_DIR/.venv/bin/python" ]]; then
  echo "Missing virtualenv python at $REPO_DIR/.venv/bin/python" >&2
  echo "Create it with: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemctl not found" >&2
  exit 1
fi

mkdir -p "$USER_SYSTEMD_DIR"

sed "s|__REPO_DIR__|$REPO_DIR|g" "$SERVICE_TEMPLATE" > "$SERVICE_FILE"
cp "$TIMER_TEMPLATE" "$TIMER_FILE"

chmod +x "$REPO_DIR/bin/farmacafe_monitor_run.sh" "$REPO_DIR/bin/farmacafe_on_change.sh"

systemctl --user daemon-reload
systemctl --user enable --now farmacafe-monitor.timer

echo "Installed user units:"
echo "  $SERVICE_FILE"
echo "  $TIMER_FILE"

echo
echo "Timer status:"
systemctl --user status farmacafe-monitor.timer --no-pager || true

echo
echo "Next runs:"
systemctl --user list-timers farmacafe-monitor.timer --all --no-pager || true

echo
echo "Optional (run timer without active login session):"
echo "  sudo loginctl enable-linger $USER"
