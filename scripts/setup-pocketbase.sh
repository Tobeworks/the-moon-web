#!/bin/sh
set -e

PB_VERSION="0.36.8"
PB_DIR="tools/pocketbase"
PB_BIN="$PB_DIR/pocketbase"

if [ -f "$PB_BIN" ]; then
  echo "PocketBase $PB_VERSION already present."
  exit 0
fi

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$ARCH" in
  x86_64)  ARCH="amd64" ;;
  arm64|aarch64) ARCH="arm64" ;;
  *)
    echo "Unsupported architecture: $ARCH"
    exit 1
    ;;
esac

URL="https://github.com/pocketbase/pocketbase/releases/download/v${PB_VERSION}/pocketbase_${PB_VERSION}_${OS}_${ARCH}.zip"

echo "Downloading PocketBase $PB_VERSION ($OS/$ARCH)..."
curl -fsSL "$URL" -o /tmp/pocketbase.zip
unzip -o /tmp/pocketbase.zip pocketbase -d "$PB_DIR"
chmod +x "$PB_BIN"
rm /tmp/pocketbase.zip

echo "PocketBase installed at $PB_BIN"
