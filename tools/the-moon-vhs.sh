#!/bin/bash
# the-moon-vhs.sh
# Apply The Moon Records video effects to a video file.
#
# Usage:
#   ./the-moon-vhs.sh input.mp4 [output.mp4]
#
# Effects applied:
#   - Scanlines (drawgrid, 1px lines / 4px rhythm — CRT phosphor row spacing)
#   - Chromatic aberration (rgbashift rh=2 bh=-2 — red right, cyan left, VHS signal bleed)
#   - Film grain / noise (temporal+uniform — worn surface, material texture)
#   - Vignette (dark edges, luminous center — screen boundary effect)
#   - Color grade (red +10%, green/blue pull — Dirty Red bias)

set -e

INPUT="$1"
OUTPUT="${2:-${INPUT%.*}_pg.mp4}"

if [ -z "$INPUT" ]; then
  echo "Usage: $0 input.mp4 [output.mp4]"
  exit 1
fi

if [ ! -f "$INPUT" ]; then
  echo "Error: file not found: $INPUT"
  exit 1
fi

echo "→ Input:  $INPUT"
echo "→ Output: $OUTPUT"
echo "→ Applying The Moon Records effects..."

ffmpeg -i "$INPUT" \
  -vf "drawgrid=x=0:y=0:width=iw:height=4:color=black@0.25:thickness=1,\
rgbashift=rh=5:gh=-1:bh=-5:enable='between(mod(t\,6)\,5.3\,5.5)+between(mod(t\,6)\,5.76\,5.86)',\
noise=alls=28:allf=t+u,\
vignette=PI/3.5,\
colorchannelmixer=rr=1.15:gg=0.94:bb=0.88" \
  -c:v libx264 -crf 18 -preset slow \
  -pix_fmt yuv420p \
  -c:a copy \
  "$OUTPUT" -y

echo "✓ Done: $OUTPUT"
