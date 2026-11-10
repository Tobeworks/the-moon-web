"""
dsp.py — find DSP links with the external dsp_scraper and add them to releases.json.
"""

import json
import subprocess
from pathlib import Path

from commands.checks import PLATFORM_NAMES
from commands.push import write_releases
from studio.config import Config

MIN_CONFIDENCE = 85


def _artist_matches(artist: str, matched: str) -> bool:
    a, m = artist.strip().lower(), (matched or "").strip().lower()
    return bool(a and m and (a in m or m in a))


def candidates(scraper_json: dict, artist: str, existing: list[dict]) -> list[dict]:
    have = {p["name"] for p in existing if p.get("url")}
    out = []
    for name in PLATFORM_NAMES:
        r = (scraper_json.get("results") or {}).get(name)
        if not r or not r.get("url") or name in have:
            continue
        conf = r.get("confidence") or 0
        matched = r.get("matched_artist") or ""
        if not matched:
            accepted, reason = False, "no matched_artist"
        elif not _artist_matches(artist, matched):
            accepted, reason = False, f"artist differs ({matched})"
        elif conf < MIN_CONFIDENCE:
            accepted, reason = False, f"confidence {conf:g} < {MIN_CONFIDENCE}"
        else:
            accepted, reason = True, ""
        out.append({"name": name, "url": r["url"], "confidence": conf,
                    "matched_artist": matched, "accepted": accepted, "reason": reason})
    return out


def scan(cfg: Config, bandcamp_url: str) -> dict:
    res = subprocess.run(["uv", "run", "python", "cli.py", bandcamp_url, "--stdout"],
                         cwd=cfg.scraper_dir, capture_output=True, text=True, timeout=240)
    if res.returncode != 0:
        raise RuntimeError((res.stderr or res.stdout).strip()[-500:] or "scraper failed")
    return json.loads(res.stdout)


def apply_links(releases_path: Path, catalog: str, links: list[dict]) -> Path:
    for link in links:
        if link.get("name") not in PLATFORM_NAMES:
            raise ValueError(f"unknown platform: {link.get('name')}")
        if not str(link.get("url") or "").strip():
            raise ValueError(f"empty URL for {link['name']}")
    data = json.loads(releases_path.read_text())
    entry = next((r for r in data["releases"] if r["catalog"] == catalog), None)
    if entry is None:
        raise KeyError(catalog)
    have = {p["name"] for p in entry["platforms"] if p.get("url")}
    entry["platforms"] = [p for p in entry["platforms"] if p.get("url")]
    for link in links:
        if link["name"] not in have:
            entry["platforms"].append({"name": link["name"], "url": link["url"].strip()})
            have.add(link["name"])
    return write_releases(releases_path, data)
