#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="farmacafe-sandbox:latest"
CONTAINERFILE="Containerfile.sandbox"
SCRIPT="farmacafe_menu_plus.py"
NO_NETWORK=0
WORK_DIR=""
AUTO_BUILD=0
FORCE_BUILD=0
SANDBOX_MODE=0

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
  --build              Force build sandbox image before running
  --auto-build         Build image if not found (default on first run)
  --image NAME         Override image name (default: farmacafe-sandbox:latest)
  --script FILE        Script to execute inside container:
                       farmacafe_menu_plus.py | farmacafe_parser_repair_helper.py
  --work-dir PATH      Mount host PATH as writable /work inside container
  --sandbox-mode       Read-only filesystem (for untrusted repaired parsers)
  --no-network         Disable network access inside container
  -h, --help           Show this help

Examples:
  ./bin/farmacafe_podman_launcher.sh --auto-build -- --json
  ./bin/farmacafe_podman_launcher.sh --script farmacafe_parser_repair_helper.py \
    --work-dir ~/.cache/farmacafe-repair -- --report-file /work/context.json
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --build)
      FORCE_BUILD=1
      shift
      ;;
    --auto-build)
      AUTO_BUILD=1
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
    --work-dir)
      WORK_DIR="$(cd -P "$2" 2>/dev/null || mkdir -p "$2" && cd -P "$2" && pwd)"
      shift 2
      ;;
    --no-network)
      NO_NETWORK=1
      shift
      ;;
    --sandbox-mode)
      SANDBOX_MODE=1
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

_image_exists() {
  podman image inspect "$IMAGE_NAME" >/dev/null 2>&1
}

_build_image() {
  echo "Building image: $IMAGE_NAME"
  podman build -t "$IMAGE_NAME" -f "$REPO_DIR/$CONTAINERFILE" "$REPO_DIR"
}

if [[ $FORCE_BUILD -eq 1 ]]; then
  _build_image
  if [[ $# -eq 0 ]]; then
    echo "Image built successfully. Run with -- [args] to execute script."
    exit 0
  fi
elif [[ $AUTO_BUILD -eq 1 ]] && ! _image_exists; then
  _build_image
elif ! _image_exists; then
  echo "Image not found: $IMAGE_NAME" >&2
  echo "Build with: $0 --build" >&2
  exit 1
fi

NETWORK_OPT=(--network slirp4netns)
if [[ $NO_NETWORK -eq 1 ]]; then
  NETWORK_OPT=(--network none)
fi

# Mount options: default state dir + optional work dir
MOUNT_OPTS=()
mkdir -p "$REPO_DIR/.state"
chmod 777 "$REPO_DIR/.state"
MOUNT_OPTS+=(--volume "$REPO_DIR/.state:/app/.state:rw")

if [[ -n "$WORK_DIR" ]]; then
  chmod o+rwx "$WORK_DIR" 2>/dev/null || true
  MOUNT_OPTS+=(--volume "$WORK_DIR:/work:rw")
fi

READONLY_OPT=()
if [[ $SANDBOX_MODE -eq 1 ]]; then
  READONLY_OPT=(--read-only)
fi

# Container security: optional read-only mode for untrusted scripts.
# Default: writable filesystem for trusted scripts (menu_plus, helper).
# Use --sandbox-mode for repaired parsers to isolate them.
exec podman run --rm \
  "${READONLY_OPT[@]}" \
  --security-opt=no-new-privileges \
  --cap-drop=ALL \
  --pids-limit=128 \
  --memory=256m \
  --cpus=1 \
  --user 1000:1000 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m \
  --tmpfs /run:rw,noexec,nosuid,nodev,size=16m \
  "${NETWORK_OPT[@]}" \
  "${MOUNT_OPTS[@]}" \
  "$IMAGE_NAME" \
  "/app/src/$SCRIPT" "$@"
