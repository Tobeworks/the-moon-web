import json

import pytest

from studio.config import Config
from studio.migrate import migrate_all, migrate_release

ENTRY = {
    "catalog": "TMR-099", "artist": "Logic Moon", "title": "Test", "format": "EP", "year": "2026",
    "genre": "Dark Ambient", "release_date": "2026-11-13T00:00:00+00:00",
    "about": "# Test\n\nPublished text.",
    "platforms": [{"name": "bandcamp", "url": "https://b"}, {"name": "spotify", "url": "https://s"}],
    "tracks": [{"number": 1, "title": "Published Title"}],
}


def load(d):
    return json.loads((d / "release.json").read_text())


def set_release(d, **changes):
    r = load(d)
    r.update(changes)
    (d / "release.json").write_text(json.dumps(r))


def test_fills_empty_fields_platforms_and_about(release_dir):
    set_release(release_dir, genre="", year=None, release_date="YYYY-MM-DD", platforms={"bandcamp": None})
    (release_dir / "about.md").write_text("# T\n\nWrite your release description here.\n")
    changes = migrate_release(ENTRY, release_dir)
    r = load(release_dir)
    assert r["genre"] == "Dark Ambient" and r["year"] == "2026" and r["release_date"] == "2026-11-13"
    assert r["platforms"] == {"bandcamp": "https://b", "spotify": "https://s"}
    assert (release_dir / "about.md").read_text() == "# Test\n\nPublished text."
    assert len(changes) >= 4


def test_never_overwrites_existing_values(release_dir):
    set_release(release_dir, genre="Ambient", artist="Local Artist", platforms={"spotify": "https://mine"})
    migrate_release(ENTRY, release_dir)
    r = load(release_dir)
    assert r["genre"] == "Ambient" and r["artist"] == "Local Artist"
    assert r["platforms"]["spotify"] == "https://mine" and r["platforms"]["bandcamp"] == "https://b"
    assert "real description" in (release_dir / "about.md").read_text()


def test_fills_only_empty_track_titles(release_dir):
    r = load(release_dir)
    r["tracks"][0]["title"] = ""
    (release_dir / "release.json").write_text(json.dumps(r))
    migrate_release(ENTRY, release_dir)
    assert load(release_dir)["tracks"][0]["title"] == "Published Title"


def test_dry_run_changes_nothing_and_second_run_is_a_noop(release_dir):
    set_release(release_dir, genre="")
    before = (release_dir / "release.json").read_text()
    assert migrate_release(ENTRY, release_dir, apply=False)
    assert (release_dir / "release.json").read_text() == before
    assert migrate_release(ENTRY, release_dir)
    assert migrate_release(ENTRY, release_dir) == []


def test_backup_is_made_once_before_the_first_change(release_dir):
    set_release(release_dir, genre="")
    original = (release_dir / "release.json").read_text()
    migrate_release(ENTRY, release_dir)
    set_release(release_dir, year="")
    migrate_release(ENTRY, release_dir)
    assert (release_dir / "release.json.before-migrate").read_text() == original


def test_migrate_all_skips_releases_without_folder_or_release_json(tmp_path, release_dir):
    import shutil
    web = tmp_path / "web"
    (web / "data").mkdir(parents=True)
    other = {**ENTRY, "catalog": "TMR-500"}
    (web / "data" / "releases.json").write_text(json.dumps({"releases": [ENTRY, other]}))
    assets = tmp_path / "assets"
    shutil.copytree(release_dir, assets / release_dir.name)
    set_release(assets / release_dir.name, genre="")
    cfg = Config(web_root=web, assets_dir=assets, scraper_dir=tmp_path)
    result = migrate_all(cfg)
    assert list(result) == ["TMR-099"] and any("genre" in c for c in result["TMR-099"])


def _setup_published(tmp_path, release_dir, entry_platforms, folder_platforms):
    import shutil
    web = tmp_path / "web"
    (web / "data").mkdir(parents=True)
    src = json.loads((__import__("pathlib").Path(__file__).parents[3] / "data" / "releases.json").read_text())
    entry = {**src["releases"][0], "catalog": "TMR-099", "platforms": entry_platforms}
    src["releases"] = [entry]
    (web / "data" / "releases.json").write_text(json.dumps(src))
    shutil.copy(__import__("pathlib").Path(__file__).parents[3] / "data" / "releases.schema.json", web / "data")
    assets = tmp_path / "assets"
    shutil.copytree(release_dir, assets / release_dir.name)
    set_release(assets / release_dir.name, platforms=folder_platforms)
    return Config(web_root=web, assets_dir=assets, scraper_dir=tmp_path), web / "data" / "releases.json"


def _platforms(path):
    return json.loads(path.read_text())["releases"][0]["platforms"]


def test_links_set_only_in_the_folder_are_added_to_releases_json(tmp_path, release_dir):
    cfg, path = _setup_published(tmp_path, release_dir, [{"name": "spotify", "url": "https://s"}],
                                 {"bandcamp": "https://b", "spotify": "https://other", "deezer": None, "tidal": "https://t"})
    result = migrate_all(cfg, apply=False)
    assert _platforms(path) == [{"name": "spotify", "url": "https://s"}]  # dry run: nothing written
    assert any("releases.json" in c and "bandcamp" in c for c in result["TMR-099"])
    migrate_all(cfg)
    assert _platforms(path) == [{"name": "spotify", "url": "https://s"}, {"name": "bandcamp", "url": "https://b"}]
    assert migrate_all(cfg) == {}  # second run: nothing left to do
