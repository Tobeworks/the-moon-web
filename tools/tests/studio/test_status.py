import json
import os
import shutil
from datetime import date
from pathlib import Path

import soundfile as sf

from studio.config import Config
from studio.status import (committed_entries, days_until, find_folder, list_releases,
                           next_step, release_status, validation_problems)

TODAY = date(2026, 11, 10)


def entry(**kw):
    e = {"catalog": "TMR-099", "artist": "A", "title": "T", "release_date": "2026-12-01",
         "pushed_at": "2026-11-01T00:00:00+00:00", "platforms": []}
    e.update(kw)
    return e


def mp3s(folder, cover_newer=False):
    for br in ("128", "320"):
        d = folder / "export" / "mp3" / br
        d.mkdir(parents=True, exist_ok=True)
        (d / "01_first.mp3").write_bytes(b"x")
    cover = next((folder / "artwork").iterdir())
    for f in folder.glob("export/mp3/*/*.mp3"):
        os.utime(f, (1000, 1000))
    os.utime(cover, (2000, 2000) if cover_newer else (500, 500))


def test_a_ok_needs_audio_and_cover(release_dir):
    assert release_status(None, release_dir, None)["A"] == "ok"
    (release_dir / "audio" / "01_first.wav").unlink()
    assert release_status(None, release_dir, None)["A"] == "open"


def test_v_stays_ok_without_about_text(release_dir):
    (release_dir / "about.md").unlink()
    assert release_status(None, release_dir, None)["V"] == "ok"


def test_v_open_with_fill_in(release_dir):
    assert release_status(None, release_dir, None)["V"] == "ok"
    p = release_dir / "release.json"
    d = json.loads(p.read_text())
    d["artist"] = "FILL_IN"
    p.write_text(json.dumps(d))
    assert release_status(None, release_dir, None)["V"] == "open"


def test_blockers_and_warnings_are_separate(tmp_path):
    from studio.folders import create_release
    from studio.status import validation_warnings
    d = create_release(tmp_path, "TMR-050", "Aethery Fields", "Old Fog Horn")  # no tracks, date, cover, about
    assert len(validation_problems(d)) == 1 and "Tracks einlesen" in validation_problems(d)[0]
    warnings = " ".join(validation_warnings(d))
    assert "Release-Datum" in warnings and "Releasetext" in warnings and "Cover-Name" in warnings
    assert validation_problems(tmp_path / "missing") == ["release.json fehlt"]


def test_fill_in_artist_is_a_blocker(release_dir):
    p = release_dir / "release.json"
    d = json.loads(p.read_text())
    d["artist"] = "FILL_IN"
    p.write_text(json.dumps(d))
    assert validation_problems(release_dir) == ["Artist fehlt"]


def test_validation_problems_empty_for_complete_release(release_dir):
    assert validation_problems(release_dir) == []


def test_missing_audio_file_is_a_problem(release_dir):
    (release_dir / "audio" / "01_first.wav").unlink()
    assert any("01_first.wav" in p for p in validation_problems(release_dir))


def test_pushed_release_does_not_count_open_a_v_k_but_keeps_stale(release_dir):
    assert release_status(entry(), release_dir, None)["V"] == "ok"
    p = release_dir / "release.json"
    d = json.loads(p.read_text())
    d["artist"] = "FILL_IN"
    p.write_text(json.dumps(d))
    s = release_status(entry(), release_dir, None)
    assert (s["A"], s["V"], s["K"]) == ("ok", "na", "na")
    mp3s(release_dir, cover_newer=True)
    assert release_status(entry(), release_dir, None)["K"] == "stale"


def test_k_stale_when_cover_newer(release_dir):
    mp3s(release_dir, cover_newer=True)
    assert release_status(None, release_dir, None)["K"] == "stale"
    mp3s(release_dir, cover_newer=False)
    assert release_status(None, release_dir, None)["K"] == "ok"


def test_k_open_when_mp3_names_do_not_match_track_titles(release_dir):
    mp3s(release_dir)
    assert release_status(None, release_dir, None)["K"] == "ok"
    p = release_dir / "release.json"
    d = json.loads(p.read_text())
    d["tracks"][0]["title"] = "Renamed"
    p.write_text(json.dumps(d))
    assert release_status(None, release_dir, None)["K"] == "open"


def test_k_open_without_mp3s(release_dir):
    assert release_status(None, release_dir, None)["K"] == "open"


def test_old_release_without_folder_is_na():
    s = release_status(entry(), None, entry())
    assert (s["A"], s["V"], s["K"], s["P"]) == ("na", "na", "na", "ok")
    assert release_status(None, None, None)["A"] == "open"


def test_g_warn_when_not_committed():
    assert release_status(entry(), None, None)["G"] == "warn"
    assert release_status(entry(), None, entry(title="old"))["G"] == "warn"
    assert release_status(entry(), None, entry())["G"] == "ok"
    assert release_status(None, None, None)["G"] == "open"


def test_d_needs_four_dsps():
    three = [{"name": n, "url": "u"} for n in ("spotify", "apple_music", "amazon_music")]
    assert release_status(entry(platforms=three), None, None)["D"] == "open"
    four = three + [{"name": "deezer", "url": "u"}]
    assert release_status(entry(platforms=four), None, None)["D"] == "ok"
    four[3]["url"] = ""
    assert release_status(entry(platforms=four), None, None)["D"] == "open"


def test_next_step_skips_na():
    s = {"A": "na", "V": "na", "K": "na", "P": "ok", "G": "warn", "D": "open"}
    assert next_step(s) == "G"
    assert next_step({k: "ok" for k in "AVKPGD"}) is None


def test_days_until_both_formats():
    assert days_until("2026-11-13", TODAY) == 3
    assert days_until("2026-11-13T00:00:00+00:00", TODAY) == 3
    assert days_until("2026-11-01", TODAY) == -9
    assert days_until(None, TODAY) is None and days_until("YYYY-MM-DD", TODAY) is None


def make_cfg(tmp_path):
    web = tmp_path / "web"
    (web / "data").mkdir(parents=True)
    (web / "data" / "releases.json").write_text(json.dumps({"releases": []}))
    assets = tmp_path / "assets"
    assets.mkdir()
    return Config(web_root=web, assets_dir=assets, scraper_dir=tmp_path / "scraper")


def test_find_folder_by_catalog(tmp_path):
    (tmp_path / "tmr-017-x-y").mkdir()
    (tmp_path / "tmr-0170-x").mkdir()
    assert find_folder(tmp_path, "TMR-017").name == "tmr-017-x-y"
    assert find_folder(tmp_path, "TMR-018") is None


def test_list_releases_includes_folder_without_entry_and_sorts(tmp_path, release_dir):
    cfg = make_cfg(tmp_path)
    shutil.copytree(release_dir, cfg.assets_dir / release_dir.name)
    data = {"releases": [entry(catalog="TMR-001", release_date="2025-01-01"),
                         entry(catalog="TMR-002", release_date="2026-05-01")]}
    cfg.releases_path.write_text(json.dumps(data))
    rows = list_releases(cfg, TODAY)
    assert [r["catalog"] for r in rows] == ["TMR-099", "TMR-002", "TMR-001"]
    assert rows[0]["next"] == "K" and rows[0]["upcoming"] is True
    assert rows[1]["upcoming"] is False and rows[1]["days_until"] < 0


def test_committed_entries_outside_git_is_empty(tmp_path):
    assert committed_entries(make_cfg(tmp_path)) == {}
