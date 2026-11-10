"""
folders.py — release folders in the-moon-assets: create, copy files, write metadata.
"""

import json
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

from studio.folders_types import AUDIO_EXT, IMAGE_EXT  # noqa: F401  (re-exported)

META_FIELDS = {"artist", "title", "release_date", "format", "genre", "year"}


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def next_catalog(entries: list[dict], assets_dir: Path) -> str:
    numbers = [int(m.group(1)) for e in entries
               if (m := re.match(r"TMR-(\d+)$", e.get("catalog", ""), re.I))]
    if assets_dir.exists():
        numbers += [int(m.group(1)) for d in assets_dir.glob("tmr-*")
                    if (m := re.match(r"tmr-(\d+)-", d.name, re.I))]
    return f"TMR-{max(numbers, default=0) + 1:03d}"


def create_release(assets_dir: Path, catalog: str, artist: str, title: str,
                   release_date: str = "") -> Path:
    prefix = catalog.lower() + "-"
    if any(d.name.lower().startswith(prefix) for d in assets_dir.glob("tmr-*")):
        raise FileExistsError(catalog)
    d = assets_dir / f"{prefix}{slug(artist)}-{slug(title)}".rstrip("-")
    (d / "audio").mkdir(parents=True)
    (d / "artwork").mkdir()
    (d / "release.json").write_text(json.dumps({
        "release_id": catalog.upper(), "catalog": catalog.upper(), "artist": artist,
        "title": title, "release_date": release_date, "label": "The Moon Records",
        "format": "EP"}, indent=2))
    return d


def classify(path: Path) -> str | None:
    ext = path.suffix.lower()
    return "audio" if ext in AUDIO_EXT else "artwork" if ext in IMAGE_EXT else None


def copy_files(release_dir: Path, sources: list[Path],
               overwrite: frozenset = frozenset()) -> dict:
    files = []
    for s in sources:
        s = Path(s)
        files += sorted(f for f in s.iterdir() if f.is_file()) if s.is_dir() else [s]
    res = {"copied": [], "conflicts": [], "skipped": [], "unchanged": []}
    for f in files:
        kind = classify(f)
        if kind is None or f.name.startswith("."):
            res["skipped"].append(f.name)
            continue
        target = release_dir / kind / f.name
        if target.exists() and f.name not in overwrite:
            same = target.stat().st_size == f.stat().st_size and target.stat().st_mtime_ns == f.stat().st_mtime_ns
            res["unchanged" if same else "conflicts"].append(f.name)  # copy2 keeps mtime: same = already there
            continue
        shutil.copy2(f, target)
        res["copied"].append(f.name)
    return res


def write_meta(release_dir: Path, fields: dict, about: str | None) -> dict:
    path = release_dir / "release.json"
    if not path.exists():
        raise ValueError("release.json missing — create the release first")
    unknown = set(fields) - META_FIELDS - {"bandcamp"}
    if unknown:
        raise ValueError(f"unknown field(s): {', '.join(sorted(unknown))}")
    release = json.loads(path.read_text())
    for k, v in fields.items():
        if k == "bandcamp":
            platforms = release.get("platforms") or {}
            platforms["bandcamp"] = v or None
            release["platforms"] = platforms
        else:
            release[k] = v
    path.write_text(json.dumps(release, indent=2))
    if about is not None:
        (release_dir / "about.md").write_text(about, encoding="utf-8")
    return release


def pick_paths(kind: str) -> list[Path]:
    """Native macOS file/folder dialog. Returns [] when cancelled."""
    if kind == "folder":
        script = 'POSIX path of (choose folder with prompt "Select folder")'
    else:
        prompt = "Select cover" if kind == "cover" else "Select files"
        multi = "" if kind == "cover" else " with multiple selections allowed"
        script = (f'set f to choose file with prompt "{prompt}"{multi}\n'
                  'set out to ""\n'
                  'repeat with i in (f as list)\nset out to out & POSIX path of i & linefeed\nend repeat\n'
                  'return out')
    res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if res.returncode != 0:
        return []
    return [Path(p) for p in res.stdout.splitlines() if p.strip()]
