"""
validate.py — The Moon Records release asset validator
Checks a release folder against the schema defined in architecture/assets.md
"""

import json
import os
import re
import sys
from pathlib import Path

from colorama import init, Fore, Style
from PIL import Image

init(autoreset=True)

REQUIRED_FIELDS = ['release_id', 'artist', 'title', 'format', 'label',
                   'catalog', 'release_date', 'tracks', 'artwork']

TRACK_REQUIRED = ['number', 'title', 'file', 'duration']

WAV_NAMING_RE = re.compile(r'^\d{2}_[a-z0-9_]+\.wav$')

MIN_COVER_SIZE = (3000, 3000)


def ok(msg):
    print(f"  {Fore.GREEN}✓{Style.RESET_ALL}  {msg}")

def fail(msg):
    print(f"  {Fore.RED}✗{Style.RESET_ALL}  {msg}")

def warn(msg):
    print(f"  {Fore.YELLOW}~{Style.RESET_ALL}  {msg}")

def header(msg):
    print(f"\n{Fore.WHITE}{Style.BRIGHT}{msg}{Style.RESET_ALL}")
    print("─" * 50)


def validate_release(release_path: str, generate_md: bool = False):
    path = Path(release_path)

    print(f"\n{Fore.RED}{Style.BRIGHT}THE MOON RECORDS — RELEASE VALIDATOR{Style.RESET_ALL}")
    print(f"Target: {path.name}\n")

    errors = []

    # ── 1. release.json ───────────────────────────────────────────────────────
    header("1. RELEASE.JSON")

    json_path = path / 'release.json'
    if not json_path.exists():
        fail("release.json not found")
        sys.exit(1)

    try:
        with open(json_path) as f:
            data = json.load(f)
        ok("release.json — valid JSON")
    except json.JSONDecodeError as e:
        fail(f"release.json — invalid JSON: {e}")
        sys.exit(1)

    # ── 2. Required fields ────────────────────────────────────────────────────
    header("2. REQUIRED FIELDS")

    for field in REQUIRED_FIELDS:
        if field not in data or data[field] in [None, '', 'YYYY-MM-DD']:
            fail(f"{field} — missing or empty")
            errors.append(field)
        else:
            ok(f"{field}: {str(data[field])[:60]}")

    # ── 3. Tracks ─────────────────────────────────────────────────────────────
    header("3. TRACKS")

    tracks = data.get('tracks', [])
    if not tracks:
        fail("No tracks defined")
        errors.append('tracks')
    else:
        ok(f"{len(tracks)} track(s) defined")

    audio_path = path / 'audio'

    for t in tracks:
        num = t.get('number', '?')
        title = t.get('title', '—')
        wav_file = t.get('file', '')

        # Required track fields
        for field in TRACK_REQUIRED:
            if not t.get(field):
                warn(f"Track {num} — '{field}' is empty")

        # WAV exists
        if wav_file:
            wav_path = audio_path / wav_file
            if wav_path.exists():
                ok(f"Track {num} — {wav_file} found")
            else:
                fail(f"Track {num} — {wav_file} NOT FOUND in audio/")
                errors.append(f'track_{num}_wav')

            # WAV naming convention
            if not WAV_NAMING_RE.match(wav_file):
                warn(f"Track {num} — '{wav_file}' doesn't match convention "
                     f"(expected: NN_title_slug.wav)")
        else:
            fail(f"Track {num} — no file defined")
            errors.append(f'track_{num}_file')

    # ── 4. Artwork ────────────────────────────────────────────────────────────
    header("4. ARTWORK")

    artwork_dir = path / 'artwork'
    pngs = sorted(artwork_dir.glob('*.png')) if artwork_dir.exists() else []
    artwork_path = pngs[0] if pngs else None

    if not artwork_path:
        fail("No PNG found in artwork/")
        errors.append('cover')
    else:
        ok(f"artwork/{artwork_path.name} found")
        try:
            with Image.open(artwork_path) as img:
                w, h = img.size
                if w >= MIN_COVER_SIZE[0] and h >= MIN_COVER_SIZE[1]:
                    ok(f"Resolution: {w}×{h}px ✓")
                else:
                    fail(f"Resolution: {w}×{h}px — minimum is 3000×3000px")
                    errors.append('cover_resolution')
        except Exception as e:
            fail(f"Could not read cover: {e}")
            errors.append('cover_read')

    # ── 5. Summary ────────────────────────────────────────────────────────────
    header("5. SUMMARY")

    if not errors:
        print(f"  {Fore.GREEN}{Style.BRIGHT}ALL CHECKS PASSED — {data.get('catalog', '')} ready.{Style.RESET_ALL}\n")
        if generate_md:
            _generate_release_md(data, path)
    else:
        print(f"  {Fore.RED}{Style.BRIGHT}{len(errors)} ERROR(S) — release not ready.{Style.RESET_ALL}")
        for e in errors:
            print(f"  {Fore.RED}→ {e}{Style.RESET_ALL}")
        print()
        sys.exit(1)


def _generate_release_md(data: dict, asset_path: Path):
    """Generate a release.md draft from validated release.json."""

    tracks_md = '\n'.join([
        f"| {t['number']} | {t.get('title','—')} | {t.get('duration','—')} |"
        for t in data.get('tracks', [])
    ])

    md = f"""# {data['catalog']} — {data['artist']} — {data['title']}

**Artist:** {data['artist']}
**Format:** {data['format']}
**Label:** {data['label']}
**Catalog:** {data['catalog']}
**Release Date:** {data.get('release_date', 'TBD')}

---

## Tracklist

| # | Title | Duration |
|---|-------|----------|
{tracks_md}

---

## Distribution

| Platform | URL |
|---|---|
| Bandcamp | {(data.get('platforms') or data.get('plaforms') or {}).get('bandcamp') or '—'} |
| Spotify | {(data.get('platforms') or data.get('plaforms') or {}).get('spotify') or '—'} |
| SoundCloud | {(data.get('platforms') or data.get('plaforms') or {}).get('soundcloud') or '—'} |

---

*Generated by tmr validate — do not edit manually.*
"""

    out_path = asset_path / 'release_draft.md'
    with open(out_path, 'w') as f:
        f.write(md)

    print(f"  {Fore.GREEN}→ Draft generated: {out_path}{Style.RESET_ALL}\n")
