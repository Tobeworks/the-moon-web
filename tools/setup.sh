#!/bin/bash
# The Moon Records Tools — setup
# Run once: bash tools/setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "→ Creating virtual environment..."
python3 -m venv venv

echo "→ Installing dependencies..."
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "→ Making pg executable..."
chmod +x pg

echo ""
echo "✓ Setup complete."
echo "  Usage: ./tools/tmr validate <release-folder-path>"
