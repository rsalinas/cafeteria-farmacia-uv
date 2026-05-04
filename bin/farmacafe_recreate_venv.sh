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

PYTHON_CMD="${PYTHON_CMD:-python3}"
RESTART_TIMER=0

usage() {
  cat <<'EOF'
Usage:
  ./bin/farmacafe_recreate_venv.sh [options]

Options:
  --python CMD       Python executable to use (default: python3 or $PYTHON_CMD)
  --restart-timer    Restart farmacafe-monitor.timer after reinstall
  -h, --help         Show this help

Examples:
  ./bin/farmacafe_recreate_venv.sh
  ./bin/farmacafe_recreate_venv.sh --python /usr/bin/python3.12 --restart-timer
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      PYTHON_CMD="$2"
      shift 2
      ;;
    --restart-timer)
      RESTART_TIMER=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
  echo "Python command not found: $PYTHON_CMD" >&2
  exit 1
fi

echo "[1/5] Removing old virtual environment"
rm -rf "$REPO_DIR/.venv"

echo "[2/5] Creating virtual environment with: $PYTHON_CMD"
"$PYTHON_CMD" -m venv "$REPO_DIR/.venv"

echo "[3/5] Upgrading pip"
"$REPO_DIR/.venv/bin/python" -m pip install --upgrade pip

echo "[4/5] Installing dependencies"
"$REPO_DIR/.venv/bin/pip" install -r "$REPO_DIR/requirements.txt"

echo "[5/5] Running health check"
"$REPO_DIR/.venv/bin/python" -c "import requests, bs4; print('OK: venv ready')"

if [[ $RESTART_TIMER -eq 1 ]]; then
  if command -v systemctl >/dev/null 2>&1; then
    echo "Restarting systemd user timer: farmacafe-monitor.timer"
    systemctl --user daemon-reload
    systemctl --user restart farmacafe-monitor.timer
    systemctl --user status farmacafe-monitor.timer --no-pager || true
  else
    echo "systemctl not found; skipped timer restart" >&2
  fi
fi

echo "Done. You can run: $REPO_DIR/bin/farmacafe --json"
