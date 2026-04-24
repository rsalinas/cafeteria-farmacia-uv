#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="farmacafe-sandbox:latest"
CONTAINERFILE="Containerfile.sandbox"
SCRIPT="farmacafe_menu_plus.py"
NO_NETWORK=0

SCRIPT_PATH="${BASH_SOURCE[0]}"
while [[ -h "$SCRIPT_PATH" ]]; do
  SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" && pwd)"
  SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
  [[ "$SCRIPT_PATH" != /* ]] && SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_PATH"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" && pwd)"
REPO_DIR="$(cd -P "$SCRIPT_DIR/.." && pwd)"

usage() {
  cat <<'EOF'
Usage:
  ./bin/farmacafe_podman_launcher.sh [options] -- [script args]

Options:
  --build              Build sandbox image before running
  --image NAME         Override image name (default: farmacafe-sandbox:latest)
  --script FILE        Script to execute inside container:
                       farmacafe_menu_plus.py | farmacafe_parser_repair_helper.py
  --no-network         Disable network access inside container
  -h, --help           Show this help

Examples:
  ./bin/farmacafe_podman_launcher.sh --build -- --json --state-file /tmp/state.json
  ./bin/farmacafe_podman_launcher.sh --script farmacafe_parser_repair_helper.py -- --report-file /tmp/report.json
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --build)
      podman build -t "$IMAGE_NAME" -f "$REPO_DIR/$CONTAINERFILE" "$REPO_DIR"
      shift
      ;;
    --image)
      IMAGE_NAME="$2"
      shift 2
      ;;
    --script)
      SCRIPT="$2"
      shift 2
      ;;
    --no-network)
      NO_NETWORK=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

case "$SCRIPT" in
  farmacafe_menu_plus.py|farmacafe_parser_repair_helper.py)
    ;;
  *)
    echo "Script not allowed: $SCRIPT" >&2
    exit 1
    ;;
esac

if ! command -v podman >/dev/null 2>&1; then
  echo "podman is required but not found in PATH" >&2
  exit 1
fi

NETWORK_OPT=(--network slirp4netns)
if [[ $NO_NETWORK -eq 1 ]]; then
  NETWORK_OPT=(--network none)
fi

# No bind mounts are used. Container gets read-only root and writable tmpfs only.
exec podman run --rm \
  --read-only \
  --security-opt=no-new-privileges \
  --cap-drop=ALL \
  --pids-limit=128 \
  --memory=256m \
  --cpus=1 \
  --user 1000:1000 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m \
  --tmpfs /run:rw,noexec,nosuid,nodev,size=16m \
  "${NETWORK_OPT[@]}" \
  "$IMAGE_NAME" \
  "/app/src/$SCRIPT" "$@"
