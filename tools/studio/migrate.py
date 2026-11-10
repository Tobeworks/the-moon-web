"""
migrate.py — carry already published data (data/releases.json) into the asset folders.

Fill-only: a value is written only where release.json / about.md is empty or still a placeholder.
Nothing that exists is overwritten. Safe to run again and again.
"""

import json
import shutil
from pathlib import Path

from commands.checks import PLATFORM_NAMES, about_is_placeholder, is_placeholder
from commands.push import write_releases
from studio.config import Config
from studio.status import find_folder

SCALARS = ("artist", "title", "release_date", "format", "genre", "year")


def migrate_release(entry: dict, folder: Path, apply: bool = True) -> list[str]:
    """Fill gaps in folder/release.json and folder/about.md from the published entry.
    Returns what was (or with apply=False would be) changed."""
    path = folder / "release.json"
    if not path.is_file():
        return []
    release = json.loads(path.read_text())
    changes = []

    for key in SCALARS:
        value = entry.get(key)
        if is_placeholder(release.get(key)) and not is_placeholder(value):
            release[key] = str(value)[:10] if key == "release_date" else value
            changes.append(f"{key}: {release[key]}")

    platforms = release.get("platforms")
    if isinstance(platforms, dict) or platforms is None:
        platforms = dict(platforms or {})
        added = [p["name"] for p in entry.get("platforms") or []
                 if p.get("url") and not platforms.get(p["name"])]
        for p in entry.get("platforms") or []:
            if p["name"] in added:
                platforms[p["name"]] = p["url"]
        if added:
            release["platforms"] = platforms
            changes.append("platforms: " + ", ".join(added))

    published_titles = {t.get("number"): t.get("title") for t in entry.get("tracks") or []}
    for track in release.get("tracks") or []:
        if not (track.get("title") or "").strip() and published_titles.get(track.get("number")):
            track["title"] = published_titles[track["number"]]
            changes.append(f"track {track['number']}: {track['title']}")

    about_path = folder / "about.md"
    current = about_path.read_text(encoding="utf-8") if about_path.exists() else ""
    write_about = about_is_placeholder(current) and not about_is_placeholder(entry.get("about"))
    if write_about:
        changes.append("about.md")

    if apply and changes:
        backup = folder / "release.json.before-migrate"
        if not backup.exists():
            shutil.copy2(path, backup)
        path.write_text(json.dumps(release, indent=2))
        if write_about:
            about_path.write_text(entry["about"], encoding="utf-8")
    return changes


def local_links_missing_in_entry(entry: dict, folder: Path) -> list[dict]:
    """Platform links set in the folder's release.json that the published entry does not have yet."""
    try:
        local = json.loads((folder / "release.json").read_text()).get("platforms")
    except (OSError, ValueError):
        return []
    if not isinstance(local, dict):
        return []
    have = {p["name"] for p in entry.get("platforms") or [] if p.get("url")}
    return [{"name": n, "url": str(u).strip()} for n, u in local.items()
            if n in PLATFORM_NAMES and str(u or "").strip() and n not in have]


def migrate_all(cfg: Config, apply: bool = True) -> dict[str, list[str]]:
    """{catalog: changes}. Both directions, fill-only: published → asset folder (release.json, about.md)
    and folder → releases.json (platform links the entry lacks)."""
    data = json.loads(cfg.releases_path.read_text())
    result, entry_changed = {}, False
    for entry in data.get("releases", []):
        folder = find_folder(cfg.assets_dir, entry["catalog"])
        if folder is None:
            continue
        changes = migrate_release(entry, folder, apply)
        links = local_links_missing_in_entry(entry, folder)
        if links:
            changes.append("releases.json ← " + ", ".join(link["name"] for link in links))
            if apply:
                entry.setdefault("platforms", [])
                entry["platforms"] = [p for p in entry["platforms"] if p.get("url")] + links
                entry_changed = True
        if changes:
            result[entry["catalog"]] = changes
    if entry_changed:
        write_releases(cfg.releases_path, data)
    return result
