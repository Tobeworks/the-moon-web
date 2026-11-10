"""
convert.py — The Moon Records MP3 converter
WAV/AIFF → MP3 320kbps + 128kbps CBR with full ID3 tagging + embedded cover art.
Also processes artwork into multi-size JPG + WebP exports.

Input:  release.json + audio/ + artwork/
Output: export/mp3/320/, export/mp3/128/, export/artwork/
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime

from colorama import init, Fore, Style
from pydub import AudioSegment
from mutagen.id3 import (
    ID3, TIT2, TPE1, TALB, TRCK, TDRC,
    TCON, TPUB, TXXX, APIC, ID3NoHeaderError
)
from mutagen.mp3 import MP3

init(autoreset=True)

AUDIO_EXTENSIONS = {'.wav', '.aif', '.aiff'}
BITRATES = {
    '320': '320k',   # full quality — archive / Bandcamp
    '128': '128k',   # web quality  — CDN player
}
ARTWORK_SIZES   = [3000, 1500, 600, 300]   # square px
ARTWORK_JPG_Q   = 92    # JPEG quality 0–95
ARTWORK_WEBP_Q  = 88    # WebP quality 0–100


def ok(msg):    print(f"  {Fore.GREEN}✓{Style.RESET_ALL}  {msg}")
def info(msg):  print(f"  {Fore.CYAN}→{Style.RESET_ALL}  {msg}")
def warn(msg):  print(f"  {Fore.YELLOW}~{Style.RESET_ALL}  {msg}")
def fail(msg):  print(f"  {Fore.RED}✗{Style.RESET_ALL}  {msg}")
def header(msg):
    print(f"\n{Fore.WHITE}{Style.BRIGHT}{msg}{Style.RESET_ALL}")
    print("─" * 50)


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '_', s)
    return s.strip('_')


def load_cover_bytes(artwork_dir: Path) -> tuple[bytes, str] | tuple[None, None]:
    """Return (bytes, mime_type) of first PNG/JPG in artwork/."""
    for ext, mime in [('*.png', 'image/png'), ('*.jpg', 'image/jpeg'),
                      ('*.jpeg', 'image/jpeg')]:
        covers = sorted(artwork_dir.glob(ext))
        if covers:
            return covers[0].read_bytes(), mime
    return None, None


def tag_mp3(mp3_path: Path, track: dict, release: dict,
            cover_bytes: bytes, cover_mime: str):
    """Write ID3 tags + cover to MP3 file."""
    try:
        tags = ID3(str(mp3_path))
    except ID3NoHeaderError:
        tags = ID3()

    year = ''
    rd = release.get('release_date', '')
    if rd and rd != 'YYYY-MM-DD':
        year = rd[:4]

    tags['TIT2'] = TIT2(encoding=3, text=track.get('title', ''))
    tags['TPE1'] = TPE1(encoding=3, text=release.get('artist', ''))
    tags['TALB'] = TALB(encoding=3, text=release.get('title', ''))
    tags['TRCK'] = TRCK(encoding=3,
                        text=f"{track.get('number', 1)}/{len(release.get('tracks', []))}")
    tags['TCON'] = TCON(encoding=3, text='Electronic')
    tags['TPUB'] = TPUB(encoding=3, text=release.get('label', 'The Moon Records'))

    if year:
        tags['TDRC'] = TDRC(encoding=3, text=year)

    catalog = release.get('catalog', '')
    if catalog:
        tags['TXXX:CATALOGNUMBER'] = TXXX(encoding=3,
                                           desc='CATALOGNUMBER',
                                           text=catalog)

    if cover_bytes:
        tags['APIC'] = APIC(
            encoding=0,
            mime=cover_mime,
            type=3,
            desc='Cover',
            data=cover_bytes
        )

    tags.save(str(mp3_path), v2_version=3)


def process_artwork(artwork_dir: Path, export_dir: Path, force: bool = False) -> list[dict]:
    """
    Resize + compress artwork into multiple sizes (JPG + WebP).
    Returns list of {size, jpg, webp} dicts for each exported size.
    """
    try:
        from PIL import Image
    except ImportError:
        fail("Pillow not installed — run: pip install Pillow")
        sys.exit(1)

    # Find source image
    source = None
    for ext in ('*.png', '*.jpg', '*.jpeg', '*.tif', '*.tiff'):
        found = sorted(artwork_dir.glob(ext))
        if found:
            source = found[0]
            break

    if not source:
        warn("No artwork found — skipping image export")
        return []

    export_dir.mkdir(parents=True, exist_ok=True)
    info(f"Source: {source.name} ({source.stat().st_size // 1024} KB)")

    img = Image.open(source).convert('RGB')
    w, h = img.size
    ok(f"Loaded {w}×{h}px")

    results = []
    for size in ARTWORK_SIZES:
        jpg_path  = export_dir / f"cover_{size}.jpg"
        webp_path = export_dir / f"cover_{size}.webp"

        if not force and jpg_path.exists() and webp_path.exists():
            warn(f"{size}px — exists, skipping (--force to overwrite)")
            results.append({'size': size, 'jpg': jpg_path.name, 'webp': webp_path.name})
            continue

        resized = img.resize((size, size), Image.LANCZOS)

        resized.save(str(jpg_path),  format='JPEG', quality=ARTWORK_JPG_Q,  optimize=True)
        resized.save(str(webp_path), format='WebP', quality=ARTWORK_WEBP_Q, method=6)

        jpg_kb  = jpg_path.stat().st_size  // 1024
        webp_kb = webp_path.stat().st_size // 1024
        ok(f"{size}px — JPG {jpg_kb} KB  |  WebP {webp_kb} KB")
        results.append({'size': size, 'jpg': jpg_path.name, 'webp': webp_path.name})

    return results


def convert_release(release_path: str, force: bool = False):
    path = Path(release_path)

    print(f"\n{Fore.RED}{Style.BRIGHT}THE MOON RECORDS — MP3 CONVERTER{Style.RESET_ALL}")
    print(f"Target: {path.name}\n")

    # ── Load release.json ──────────────────────────────────────────────────────
    header("1. RELEASE DATA")

    json_path = path / 'release.json'
    if not json_path.exists():
        fail("release.json not found — run generate first")
        sys.exit(1)

    with open(json_path) as f:
        release = json.load(f)

    artist  = release.get('artist', 'UNKNOWN')
    title   = release.get('title',  'UNKNOWN')
    catalog = release.get('catalog', 'TMR-XXX')
    tracks  = release.get('tracks', [])

    ok(f"{catalog} — {artist} — {title}")
    ok(f"{len(tracks)} track(s)")

    # ── Artwork ────────────────────────────────────────────────────────────────
    header("2. ARTWORK")

    artwork_dir      = path / 'artwork'
    artwork_export   = path / 'export' / 'artwork'
    cover_bytes, cover_mime = load_cover_bytes(artwork_dir)

    if cover_bytes:
        ok(f"Cover for ID3 tags: {len(cover_bytes) // 1024} KB, {cover_mime}")
    else:
        warn("No cover found — MP3s will have no embedded artwork")

    process_artwork(artwork_dir, artwork_export, force=force)

    # ── Convert ────────────────────────────────────────────────────────────────
    header("3. CONVERTING")

    audio_dir = path / 'audio'

    total_converted = 0
    total_skipped   = 0
    total_errors    = 0

    for bitrate_label, bitrate_value in BITRATES.items():
        info(f"Bitrate: {bitrate_value}")
        output_dir = path / 'export' / 'mp3' / bitrate_label
        output_dir.mkdir(parents=True, exist_ok=True)

        converted = 0
        skipped   = 0
        errors    = 0

        for track in tracks:
            src_file = track.get('file')
            if not src_file:
                warn(f"  Track {track.get('number')} — no file defined, skipping")
                continue

            src_path = audio_dir / src_file
            if not src_path.exists():
                fail(f"  Track {track.get('number')} — {src_file} not found")
                errors += 1
                continue

            num      = str(track.get('number', 0)).zfill(2)
            slug     = slugify(track.get('title', src_path.stem))
            out_name = f"{num}_{slug}.mp3"
            out_path = output_dir / out_name

            if out_path.exists() and not force:
                warn(f"  Track {track.get('number')} [{bitrate_label}] — {out_name} exists, skipping")
                skipped += 1
                continue

            info(f"  Track {track.get('number')} [{bitrate_label}] — {src_file} → {out_name}")

            try:
                suffix = src_path.suffix.lower()
                if suffix == '.wav':
                    audio = AudioSegment.from_wav(str(src_path))
                elif suffix in ('.aif', '.aiff'):
                    audio = AudioSegment.from_aiff(str(src_path))
                else:
                    audio = AudioSegment.from_file(str(src_path))

                audio.export(str(out_path), format='mp3', bitrate=bitrate_value)
                tag_mp3(out_path, track, release, cover_bytes, cover_mime)

                size_mb = out_path.stat().st_size / (1024 * 1024)
                ok(f"  Track {track.get('number')} [{bitrate_label}] — {out_name} ({size_mb:.1f} MB)")
                converted += 1

            except Exception as e:
                fail(f"  Track {track.get('number')} [{bitrate_label}] — failed: {e}")
                errors += 1

        total_converted += converted
        total_skipped   += skipped
        total_errors    += errors

    # ── Summary ────────────────────────────────────────────────────────────────
    header("4. SUMMARY")

    ok(f"{total_converted} MP3(s) converted ({', '.join(BITRATES.keys())}kbps)")
    ok(f"Artwork variants → {artwork_export}")
    if total_skipped:
        warn(f"{total_skipped} skipped (already exist)")
    if total_errors:
        fail(f"{total_errors} error(s)")

    print()
