"""
status.py — release status computed from files (releases.json, asset folders, git).
No state of its own: nothing here can drift from the real files.
"""

import json
import re
import subprocess
from datetime import date
from pathlib import Path

from commands.checks import about_is_placeholder, is_placeholder, publish_problems, publish_warnings
from commands.convert import cover_is_newer, mp3_name
from studio.config import Config
from studio.folders_types import AUDIO_EXT, IMAGE_EXT

STEPS = ("A", "V", "K", "P", "G", "D")
DSP_REQUIRED = ("spotify", "apple_music", "amazon_music", "deezer")


def find_folder(assets_dir: Path, catalog: str) -> Path | None:
    prefix = catalog.lower() + "-"
    return next((d for d in sorted(assets_dir.glob("tmr-*")) if d.is_dir()
                 and d.name.lower().startswith(prefix)), None)


def _files(folder: Path, exts) -> list[Path]:
    return [f for f in folder.glob("*") if f.suffix.lower() in exts and not f.name.startswith(".")]


def _read_release(folder: Path) -> dict | None:
    try:
        return json.loads((folder / "release.json").read_text())
    except (OSError, ValueError):
        return None


def _step_assets(folder: Path) -> str:
    ok = _files(folder / "audio", AUDIO_EXT) and _files(folder / "artwork", IMAGE_EXT)
    return "ok" if ok else "open"


PROBLEM_DE = {"artist": "Artist fehlt", "title": "Titel fehlt", "catalog": "Katalognummer fehlt"}
WARNING_DE = {
    "release_date": "Kein Release-Datum: gilt sofort als veröffentlicht",
    "artwork.cover": "Cover-Name nicht gesetzt („Tracks einlesen“ trägt ihn ein)",
    "about.md": "Kein Releasetext: der Text auf der Website bleibt leer",
}


def _release_and_about(folder: Path):
    about_path = folder / "about.md"
    return _read_release(folder), about_path.read_text(encoding="utf-8") if about_path.exists() else ""


def _with_live_entry(release: dict, about: str, entry: dict | None):
    """For a live release the entry is the truth: placeholders in the folder don't count."""
    if entry:
        release = {**release, **{k: entry[k] for k in ("artist", "title", "release_date")
                                 if is_placeholder(release.get(k)) and not is_placeholder(entry.get(k))}}
        if about_is_placeholder(about) and not about_is_placeholder(entry.get("about")):
            about = entry["about"]
    return release, about


def validation_warnings(folder: Path | None, entry: dict | None = None) -> list[str]:
    """Hints that do not block a push, in plain German."""
    if entry:  # live: judge the entry's own text and date, not the folder's
        release = {"release_date": entry.get("release_date"), "artwork": {"cover": "set"}}
        about = entry.get("about") or ""
    else:
        release, about = _release_and_about(folder) if folder else ({}, "")
        release = release or {}
    return [WARNING_DE.get(w.split(" ")[0], w) for w in publish_warnings(release, about)]


def validation_problems(folder: Path, entry: dict | None = None) -> list[str]:
    """What blocks a push: missing basics, in plain German. Empty list = ready."""
    release, about = _release_and_about(folder)
    if release is None:
        return ["release.json fehlt"]
    release, about = _with_live_entry(release, about, entry)
    problems = [PROBLEM_DE.get(p.split(" ")[0], p) for p in publish_problems(release, about)]
    tracks = release.get("tracks") or []
    if not tracks:
        problems.append("Keine Tracks: Audiodateien hinzufügen und „Tracks einlesen“ klicken")
    problems += [f"Audiodatei fehlt: {t.get('file', '?')}" for t in tracks
                 if not (folder / "audio" / t.get("file", "")).is_file()]
    return problems


def _step_validated(folder: Path) -> str:
    return "open" if validation_problems(folder) else "ok"


def _step_converted(folder: Path) -> str:
    release = _read_release(folder) or {}
    tracks = release.get("tracks") or []
    if not tracks:
        return "open"
    found = []
    for br in ("128", "320"):
        d = folder / "export" / "mp3" / br
        for t in tracks:
            hit = d / mp3_name(t, Path(t.get("file", "")).stem)
            if not hit.is_file():
                return "open"
            found.append(hit)
    return "stale" if cover_is_newer(folder / "artwork", found) else "ok"


def release_status(entry: dict | None, folder: Path | None, committed: dict | None) -> dict:
    s = {}
    if folder is None:
        s["A"] = s["V"] = s["K"] = "na" if entry else "open"
    else:
        s["A"], s["V"], s["K"] = _step_assets(folder), _step_validated(folder), _step_converted(folder)
    s["P"] = "ok" if entry and entry.get("pushed_at") else "open"
    if s["P"] == "ok":  # already published: unfinished A/V/K of old releases are history, not to-dos
        for k in "AVK":
            if s[k] == "open":
                s[k] = "na"
    if not entry:
        s["G"] = "open"
    else:
        s["G"] = "ok" if committed is not None and committed == entry else "warn"
    have = {p["name"] for p in (entry or {}).get("platforms", []) if p.get("url")}
    s["D"] = "ok" if entry and all(n in have for n in DSP_REQUIRED) else "open"
    return s


def next_step(status: dict) -> str | None:
    return next((k for k in STEPS if status[k] not in ("ok", "na")), None)


def _date(value) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def days_until(release_date: str | None, today: date) -> int | None:
    d = _date(release_date) if release_date else None
    return (d - today).days if d else None


def committed_entries(cfg: Config) -> dict:
    """catalog → entry as in the last commit of data/releases.json ({} if unavailable)."""
    try:
        out = subprocess.run(
            ["git", "-C", str(cfg.web_root), "show", "HEAD:data/releases.json"],
            capture_output=True, text=True, check=True, timeout=10).stdout
        return {r["catalog"]: r for r in json.loads(out)["releases"]}
    except (subprocess.SubprocessError, OSError, ValueError, KeyError):
        return {}


def list_releases(cfg: Config, today: date) -> list[dict]:
    entries = json.loads(cfg.releases_path.read_text()).get("releases", [])
    committed = committed_entries(cfg)
    rows, seen = [], set()
    for e in entries:
        seen.add(e["catalog"].upper())
        rows.append((e, find_folder(cfg.assets_dir, e["catalog"]), e["catalog"]))
    for d in sorted(cfg.assets_dir.glob("tmr-*")):
        m = re.match(r"tmr-(\d+)-", d.name, re.I)
        if m and d.is_dir() and f"TMR-{m.group(1)}".upper() not in seen:
            rows.append((None, d, f"TMR-{m.group(1)}"))

    out = []
    for e, folder, catalog in rows:
        meta = e or (_read_release(folder) or {})
        st = release_status(e, folder, committed.get(catalog))
        rd = meta.get("release_date")
        days = days_until(rd, today)
        out.append({
            "catalog": catalog, "artist": meta.get("artist", ""), "title": meta.get("title", ""),
            "release_date": rd if _date(rd) else None, "days_until": days,
            "upcoming": days is not None and days > 0,
            "status": st, "next": next_step(st),
        })
    out.sort(key=lambda r: _date(r["release_date"]) or date.max, reverse=True)
    return out
