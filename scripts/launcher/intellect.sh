#!/usr/bin/env bash
set -Eeuo pipefail

LAUNCHER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${INTELLECT_ROOT:-$LAUNCHER_DIR}"
if [[ -z "${INTELLECT_ROOT:-}" ]]; then
  while [[ "$ROOT_DIR" != / && ! -f "$ROOT_DIR/pyproject.toml" ]]; do
    ROOT_DIR="$(dirname "$ROOT_DIR")"
  done
fi
if [[ ! -f "$ROOT_DIR/pyproject.toml" || ! -f "$ROOT_DIR/scripts/dev.sh" || ! -d "$ROOT_DIR/frontend" ]]; then
  echo "Keep the launcher inside the Intellect repository, or set INTELLECT_ROOT to its path." >&2
  exit 1
fi

case "${1:-}" in
  --check) printf '%s\n' "$ROOT_DIR"; exit 0 ;;
  '') ;;
  *) echo 'Supported option: --check.' >&2; exit 2 ;;
esac

# Finder starts applications with a minimal PATH.
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"
if [[ "$LAUNCHER_DIR" == */Contents/MacOS ]]; then
  exec osascript "$LAUNCHER_DIR/../Resources/open-terminal.applescript" "$ROOT_DIR/scripts/dev.sh"
fi
cd "$ROOT_DIR"
exec bash "$ROOT_DIR/scripts/dev.sh"
