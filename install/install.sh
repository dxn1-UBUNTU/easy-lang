#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${METRIX_REPO_URL:-https://github.com/dxn1-UBUNTU/METRIX.git}"
INSTALL_DIR="${METRIX_INSTALL_DIR:-$HOME/.metrix-lang}"
BIN_DIR="${METRIX_BIN_DIR:-$HOME/.local/bin}"

if ! command -v git >/dev/null 2>&1; then
  echo "METRIX installer needs git." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "METRIX installer needs python3." >&2
  exit 1
fi

mkdir -p "$BIN_DIR"

case "$INSTALL_DIR" in
  ""|"/"|"$HOME"|"$HOME/"|"/home"|"/home/")
    echo "Refusing unsafe METRIX_INSTALL_DIR: $INSTALL_DIR" >&2
    exit 1
    ;;
esac

if [ -d "$INSTALL_DIR/.git" ]; then
  git -C "$INSTALL_DIR" pull --ff-only
else
  rm -rf "$INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/python" -m pip install -e "$INSTALL_DIR"
ln -sf "$INSTALL_DIR/.venv/bin/metrix" "$BIN_DIR/metrix"

echo "METRIX installed."
echo "Command: $BIN_DIR/metrix"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    echo "Add this to your shell profile if metrix is not found:"
    echo "export PATH=\"$BIN_DIR:\$PATH\""
    ;;
esac
