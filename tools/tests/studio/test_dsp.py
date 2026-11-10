import json
import shutil
from pathlib import Path

import pytest

from studio.dsp import apply_links, candidates

REPO_DATA = Path(__file__).parents[3] / "data"

SAMPLE = {"results": {
    "spotify": {"url": "https://open.spotify.com/album/1", "matched_artist": "Logic Moon", "confidence": 100.0},
    "apple_music": {"url": "https://music.apple.com/x", "matched_artist": "Logic Moon", "confidence": 71.0},
    "deezer": {"url": None, "matched_artist": None, "confidence": 16.8},
    "amazon_music": {"url": "https://music.amazon.com/albums/1", "matched_artist": "Someone Else", "confidence": 99.0},
    "soundcloud": {"url": "https://soundcloud.com/a/b", "matched_artist": "", "confidence": 100.0},
    "youtube_music": {"url": "https://music.youtube.com/x", "matched_artist": "Logic Moon", "confidence": 100.0},
}}


def by_name(items):
    return {c["name"]: c for c in items}


def test_accepts_only_high_confidence_with_artist():
    c = by_name(candidates(SAMPLE, "Logic Moon", []))
    assert c["spotify"]["accepted"] is True
    assert c["apple_music"]["accepted"] is False and "71" in c["apple_music"]["reason"]
    assert "deezer" not in c and "youtube_music" not in c


def test_artist_mismatch_and_missing_artist_not_accepted():
    c = by_name(candidates(SAMPLE, "Logic Moon", []))
    assert c["amazon_music"]["accepted"] is False and "artist" in c["amazon_music"]["reason"]
    assert c["soundcloud"]["accepted"] is False


def test_existing_platform_is_skipped_but_empty_placeholder_is_not():
    existing = [{"name": "spotify", "url": "x"}, {"name": "apple_music", "url": ""}]
    c = by_name(candidates(SAMPLE, "Logic Moon", existing))
    assert "spotify" not in c and "apple_music" in c


@pytest.fixture
def releases(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    shutil.copy(REPO_DATA / "releases.schema.json", d)
    shutil.copy(REPO_DATA / "releases.json", d)
    return d / "releases.json"


def test_apply_appends_and_keeps_order(releases):
    data = json.loads(releases.read_text())
    cat = next(r["catalog"] for r in data["releases"]
               if not any(p["name"] == "deezer" for p in r["platforms"]))
    before = [p["name"] for r in data["releases"] if r["catalog"] == cat for p in r["platforms"]]
    backup = apply_links(releases, cat, [{"name": "deezer", "url": "https://deezer.com/album/1"}])
    after = next(r for r in json.loads(releases.read_text())["releases"] if r["catalog"] == cat)
    assert [p["name"] for p in after["platforms"]] == before + ["deezer"]
    assert backup.exists()


def test_apply_rejects_bad_input(releases):
    cat = json.loads(releases.read_text())["releases"][0]["catalog"]
    with pytest.raises(ValueError):
        apply_links(releases, cat, [{"name": "spotify", "url": ""}])
    with pytest.raises(ValueError):
        apply_links(releases, cat, [{"name": "tidal", "url": "https://x"}])
    with pytest.raises(KeyError):
        apply_links(releases, "TMR-999", [{"name": "deezer", "url": "https://x"}])
