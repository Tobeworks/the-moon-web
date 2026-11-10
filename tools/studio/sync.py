"""
sync.py — pass edits of an already published release on to data/releases.json (no CDN upload).

Only what the user changed in this save is passed on, never a placeholder or an empty value, so a
save can't replace good published data with stale or file-derived values.
"""

import json
from pathlib import Path

from commands.checks import about_is_placeholder, is_placeholder
from commands.push import write_releases

SCALARS = ("artist", "title", "format", "genre", "year")


def sync_published(releases_path: Path, catalog: str, changed: dict, about: str | None) -> list[str]:
    """Apply `changed` form fields (and a changed about text) to the entry. Returns the synced field names."""
    data = json.loads(releases_path.read_text())
    entry = next((r for r in data["releases"] if r["catalog"] == catalog), None)
    if entry is None:
        return []
    done = []

    for key in SCALARS:
        value = changed.get(key)
        if not is_placeholder(value) and entry.get(key) != value:
            entry[key] = value
            done.append(key)

    date = changed.get("release_date")
    if not is_placeholder(date) and str(entry.get("release_date", ""))[:10] != str(date)[:10]:
        entry["release_date"] = str(date)[:10]
        done.append("release_date")

    url = (changed.get("bandcamp") or "").strip()
    if url:
        platforms = entry.setdefault("platforms", [])
        current = next((p for p in platforms if p["name"] == "bandcamp"), None)
        if current is None:
            platforms.append({"name": "bandcamp", "url": url})
            done.append("bandcamp")
        elif current.get("url") != url:
            current["url"] = url
            done.append("bandcamp")

    titles = {str(n): t.strip() for n, t in (changed.get("track_titles") or {}).items() if str(t).strip()}
    renamed = False
    for track in entry.get("tracks") or []:
        new = titles.get(str(track.get("number")))
        if new and track.get("title") != new:
            track["title"] = new
            renamed = True
    if renamed:
        done.append("track_titles")

    if about is not None and not about_is_placeholder(about) and entry.get("about") != about:
        entry["about"] = about
        done.append("about")

    if done:
        write_releases(releases_path, data)
    return done
