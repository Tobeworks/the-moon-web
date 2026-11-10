#!/bin/bash
# Push all releases: generate → convert → push

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS_DIR="$SCRIPT_DIR/../../the-moon-assets"
TMR="$SCRIPT_DIR/tmr"

RELEASES=(
  "tmr-001-logic-moon-music-for-film-vol-1"
  "tmr-002-logic-moon-glow"
  "tmr-003-logic-moon-atlas"
  "tmr-004-logic-moon-memories-of-tomorrow"
  "tmr-005-logic-moon-metamorphosis"
  "tmr-006-logic-moon-heim"
  "tmr-007-logic-moon-reminiscence"
  "tmr-008-aethery-fields-debut"
  "tmr-009-aethery-fields-hello"
  "tmr-010-logic-moon-it-may-never-coming-back"
  "tmr-011-logic-moon-clockworks"
)

for release in "${RELEASES[@]}"; do
  path="$ASSETS_DIR/$release/"
  echo ""
  echo "════════════════════════════════════════"
  echo "  $release"
  echo "════════════════════════════════════════"

  echo "→ generate"
  "$TMR" generate "$path" || { echo "✗ generate failed — aborting $release"; continue; }

  echo "→ convert"
  "$TMR" convert "$path" || { echo "✗ convert failed — aborting $release"; continue; }

  echo "→ push"
  "$TMR" push "$path" || { echo "✗ push failed — aborting $release"; continue; }

  echo "✓ done: $release"
done

echo ""
echo "All releases processed."
