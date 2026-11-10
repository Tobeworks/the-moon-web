"""
generate.py — The Moon Records release.json generator
Scans audio/ folder for WAV/AIFF files and generates a pre-filled release.json.
"""

import json
import os
import re
import sys
from pathlib import Path

import soundfile as sf
from colorama import init, Fore, Style

init(autoreset=True)

AUDIO_EXTENSIONS = {'.wav', '.aif', '.aiff'}


def ok(msg):
    print(f"  {Fore.GREEN}✓{Style.RESET_ALL}  {msg}")

def info(msg):
    print(f"  {Fore.CYAN}→{Style.RESET_ALL}  {msg}")

def warn(msg):
    print(f"  {Fore.YELLOW}~{Style.RESET_ALL}  {msg}")

def fail(msg):
    print(f"  {Fore.RED}✗{Style.RESET_ALL}  {msg}")

def header(msg):
    print(f"\n{Fore.WHITE}{Style.BRIGHT}{msg}{Style.RESET_ALL}")
    print("─" * 50)


def slugify(name: str) -> str:
    """Extract track title from filename stem."""
    if ' - ' in name:
        # Take the last segment: "07 - Aethery Fields - Plume Atoll" → "Plume Atoll"
        title = name.split(' - ')[-1]
        # Strip leading track number if present: "01 Réunion" → "Réunion"
        title = re.sub(r'^\d+\s+', '', title)
        return title.strip()
    # Fallback: remove leading number+underscore, replace separators
    name = re.sub(r'^\d+_', '', name)
    return name.replace('_', ' ').replace('-', ' ').title()


def format_duration(seconds: float) -> str:
    """Convert seconds to M:SS format."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}"


def generate_release(release_path: str):
    path = Path(release_path)
    audio_path = path / 'audio'

    print(f"\n{Fore.RED}{Style.BRIGHT}THE MOON RECORDS — RELEASE GENERATOR{Style.RESET_ALL}")
    print(f"Target: {path.name}\n")

    # ── Scan audio folder ─────────────────────────────────────────────────────
    header("1. SCANNING AUDIO/")

    if not audio_path.exists():
        fail("audio/ folder not found")
        sys.exit(1)

    audio_files = sorted([
        f for f in audio_path.iterdir()
        if f.suffix.lower() in AUDIO_EXTENSIONS
    ])

    if not audio_files:
        fail("No WAV or AIFF files found in audio/")
        sys.exit(1)

    ok(f"{len(audio_files)} audio file(s) found")

    # ── Scan artwork folder ───────────────────────────────────────────────────
    ARTWORK_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.tif', '.tiff'}
    artwork_path = path / 'artwork'
    cover_file = None

    if artwork_path.exists():
        candidates = [
            f for f in artwork_path.iterdir()
            if f.suffix.lower() in ARTWORK_EXTENSIONS and not f.name.startswith('.')
        ]
        if candidates:
            cover_file = sorted(candidates)[0].name
            ok(f"Artwork found: {cover_file}")
        else:
            warn("artwork/ folder is empty")
    else:
        warn("artwork/ folder not found")

    # ── Read file metadata ────────────────────────────────────────────────────
    header("2. READING FILE METADATA")

    tracks = []
    for i, f in enumerate(audio_files, 1):
        try:
            audio_info = sf.info(str(f))
            duration = format_duration(audio_info.duration)
            sample_rate = audio_info.samplerate
            subtype = audio_info.subtype  # e.g. PCM_24

            # Extract bit depth from subtype string
            bit_depth_match = re.search(r'(\d+)', subtype)
            bit_depth = int(bit_depth_match.group(1)) if bit_depth_match else None

            track = {
                "number": i,
                "title": slugify(f.stem),
                "file": f.name,
                "duration": duration,
                "_meta": {
                    "sample_rate": sample_rate,
                    "bit_depth": bit_depth,
                    "format": f.suffix.lstrip('.').upper()
                }
            }
            tracks.append(track)

            ok(f"Track {i}: {f.name} | {duration} | {sample_rate}Hz | {bit_depth}bit")

        except Exception as e:
            fail(f"Could not read {f.name}: {e}")

    # ── Check for existing release.json ──────────────────────────────────────
    header("3. GENERATING RELEASE.JSON")

    json_path = path / 'release.json'
    existing = {}

    if json_path.exists():
        try:
            with open(json_path) as jf:
                existing = json.load(jf)
            warn("Existing release.json found — merging (preserving manual fields)")
        except Exception:
            warn("Existing release.json could not be read — overwriting")

    # Derive folder slug for catalog number
    folder_name = path.name  
    catalog_match = re.match(r'^(tmr-\d+)', folder_name, re.IGNORECASE)
    catalog = catalog_match.group(1).upper() if catalog_match else "TMR-XXX"

    # Build release.json — preserve existing manual values where set
    release = {
        "release_id":   existing.get('release_id') or catalog,
        "artist":       existing.get('artist') or "FILL_IN",
        "title":        existing.get('title') or "FILL_IN",
        "format":       existing.get('format') or "EP",
        "label":        existing.get('label') or "The Moon Records",
        "catalog":      existing.get('catalog') or catalog,
        "release_date": existing.get('release_date') or "YYYY-MM-DD",
        "tracks":       tracks,
        "artwork": existing.get('artwork') or {
            "cover": cover_file or "FILL_IN",
            "min_resolution": "3000x3000",
            "format": "PNG or TIFF"
        },
        "platforms": existing.get('platforms') or existing.get('plaforms') or {
            "bandcamp": None,
            "spotify": None,
            "soundcloud": None
        },
        "notes": existing.get('notes') or ""
    }

    with open(json_path, 'w') as jf:
        json.dump(release, jf, indent=2)

    ok(f"release.json written → {json_path}")

    # ── Create about.md placeholder ───────────────────────────────────────────
    about_path = path / 'about.md'
    if not about_path.exists():
        about_path.write_text(
            f"# {existing.get('title') or 'Release Title'}\n\n"
            "Write your release description here.\n"
        )
        ok(f"about.md created → {about_path}")
    else:
        info("about.md already exists — skipping")

    # ── Summary ───────────────────────────────────────────────────────────────
    header("4. WHAT STILL NEEDS MANUAL INPUT")

    manual_fields = []
    if release['artist'] == 'FILL_IN':
        manual_fields.append('artist')
    if release['title'] == 'FILL_IN':
        manual_fields.append('title')
    if release['release_date'] == 'YYYY-MM-DD':
        manual_fields.append('release_date')
    if release['artwork']['cover'] == 'FILL_IN':
        manual_fields.append('artwork.cover')

    for f in manual_fields:
        warn(f)

    print(f"\n  {Fore.GREEN}{Style.BRIGHT}Done. Edit release.json then run: ./tools/tmr validate{Style.RESET_ALL}\n")
