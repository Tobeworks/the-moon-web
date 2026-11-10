"""
published.py — once a release is live, data/releases.json is the only source of truth.

view():         what the form shows (published entry if there is one, else the folder's release.json)
update_entry(): save the form into the entry (no CDN upload); the folder files are not touched
"""

import json
from pathlib import Path

from commands.checks import about_is_placeholder, is_placeholder
from commands.convert import mp3_name
from commands.push import write_releases


def _folder_release(folder: Path | None) -> dict:
    try:
        return json.loads((folder / "release.json").read_text())
    except (OSError, ValueError, TypeError):
        return {}


def _folder_about(folder: Path | None) -> str:
    path = folder / "about.md" if folder else None
    return path.read_text(encoding="utf-8") if path and path.exists() else ""


def view(folder: Path | None, entry: dict | None) -> dict:
    """{"release", "about", "tracks"} for the Studio form. tracks: number, title, file, duration, mp3."""
    local = _folder_release(folder)
    if entry is None:
        tracks = [{"number": t.get("number"), "title": t.get("title", ""), "file": t.get("file", ""),
                   "duration": t.get("duration", ""), "mp3": mp3_name(t, Path(t.get("file", "")).stem)}
                  for t in local.get("tracks") or []]
        return {"release": local, "about": _folder_about(folder), "tracks": tracks}

    files = {t.get("number"): t.get("file", "") for t in local.get("tracks") or []}
    durations = {t.get("number"): t.get("duration", "") for t in local.get("tracks") or []}
    tracks = [{"number": t.get("number"), "title": t.get("title", ""), "file": files.get(t.get("number"), ""),
               "duration": t.get("runtime") or durations.get(t.get("number"), ""),
               "mp3": Path(t.get("url") or "").name or mp3_name(t)}
              for t in entry.get("tracks") or []]
    bandcamp = next((p["url"] for p in entry.get("platforms") or [] if p["name"] == "bandcamp" and p.get("url")), "")
    release = {k: entry.get(k, "") for k in ("catalog", "artist", "title", "format", "genre", "year")}
    release.update(release_date=str(entry.get("release_date") or "")[:10], platforms={"bandcamp": bandcamp},
                   tracks=tracks)
    return {"release": release, "about": entry.get("about") or "", "tracks": tracks}


def update_entry(releases_path: Path, catalog: str, fields: dict, about: str | None) -> list[str]:
    """Write form values into the published entry. Returns the names of fields that really changed.
    artist, title and date are never replaced by a placeholder or empty value."""
    data = json.loads(releases_path.read_text())
    entry = next((r for r in data["releases"] if r["catalog"] == catalog), None)
    if entry is None:
        raise KeyError(catalog)
    done = []

    for key in ("artist", "title"):
        value = str(fields.get(key) or "").strip()
        if key in fields and not is_placeholder(value) and entry.get(key) != value:
            entry[key] = value
            done.append(key)

    date = fields.get("release_date")
    if not is_placeholder(date) and str(entry.get("release_date") or "")[:10] != str(date)[:10]:
        entry["release_date"] = str(date)[:10]
        done.append("release_date")

    for key in ("format", "genre", "year"):
        if key in fields and fields[key] is not None and entry.get(key) != str(fields[key]).strip():
            entry[key] = str(fields[key]).strip()
            done.append(key)

    if "bandcamp" in fields:
        url = (fields["bandcamp"] or "").strip()
        platforms = entry.setdefault("platforms", [])
        current = next((p for p in platforms if p["name"] == "bandcamp"), None)
        if url and current is None:
            platforms.append({"name": "bandcamp", "url": url})
            done.append("bandcamp")
        elif url and current.get("url") != url:
            current["url"] = url
            done.append("bandcamp")
        elif not url and current is not None:
            platforms.remove(current)
            done.append("bandcamp")

    titles = {str(n): str(t).strip() for n, t in (fields.get("track_titles") or {}).items() if str(t).strip()}
    renamed = False
    for track in entry.get("tracks") or []:
        new = titles.get(str(track.get("number")))
        if new and track.get("title") != new:
            track["title"] = new
            renamed = True
    if renamed:
        done.append("track_titles")

    if about is not None:
        text = "" if about_is_placeholder(about) else about
        if (entry.get("about") or "") != text:
            entry["about"] = text
            done.append("about")

    if done:
        write_releases(releases_path, data)
    return done
