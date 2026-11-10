import json

from studio.sync import sync_published


def entry_of(cfg, catalog):
    return next(r for r in json.loads(cfg.releases_path.read_text())["releases"] if r["catalog"] == catalog)


def with_entry(cfg, **changes):
    """Put a TMR-099 copy of a real, schema-valid entry on top of the temp releases.json."""
    data = json.loads(cfg.releases_path.read_text())
    e = {**data["releases"][0], "catalog": "TMR-099", "platforms": [], "about": "Old text.",
         "title": "Published Title", "tracks": [{"number": 1, "title": "Pub One", "runtime": "1:00", "url": "", "url_320": ""}]}
    e.update(changes)
    data["releases"].insert(0, e)
    cfg.releases_path.write_text(json.dumps(data))


def test_new_bandcamp_url_is_appended(studio_env):
    with_entry(studio_env)
    assert sync_published(studio_env.releases_path, "TMR-099", {"bandcamp": "https://x.bandcamp.com/album/y"}, None) == ["bandcamp"]
    assert entry_of(studio_env, "TMR-099")["platforms"] == [{"name": "bandcamp", "url": "https://x.bandcamp.com/album/y"}]


def test_changed_bandcamp_url_replaces_the_old_one_and_keeps_other_links(studio_env):
    with_entry(studio_env, platforms=[{"name": "spotify", "url": "https://s"}, {"name": "bandcamp", "url": "https://old"}])
    sync_published(studio_env.releases_path, "TMR-099", {"bandcamp": "https://new"}, None)
    assert entry_of(studio_env, "TMR-099")["platforms"] == [
        {"name": "spotify", "url": "https://s"}, {"name": "bandcamp", "url": "https://new"}]


def test_text_fields_track_titles_and_date(studio_env):
    with_entry(studio_env)
    done = sync_published(studio_env.releases_path, "TMR-099",
                          {"genre": "Ambient", "release_date": "2026-12-01", "track_titles": {"1": "New One"}},
                          "# T\n\nNew text.")
    e = entry_of(studio_env, "TMR-099")
    assert e["genre"] == "Ambient" and e["release_date"] == "2026-12-01"
    assert e["tracks"][0]["title"] == "New One" and e["about"] == "# T\n\nNew text."
    assert set(done) == {"genre", "release_date", "track_titles", "about"}


def test_placeholders_and_empty_values_never_overwrite_published_data(studio_env):
    with_entry(studio_env)
    done = sync_published(studio_env.releases_path, "TMR-099",
                          {"title": "FILL_IN", "genre": "", "bandcamp": ""},
                          "# T\n\nWrite your release description here.\n")
    assert done == [] and entry_of(studio_env, "TMR-099")["title"] == "Published Title"
    assert entry_of(studio_env, "TMR-099")["about"] == "Old text."


def test_unknown_release_or_nothing_changed_writes_nothing(studio_env):
    before = studio_env.releases_path.read_text()
    assert sync_published(studio_env.releases_path, "TMR-500", {"genre": "Ambient"}, None) == []
    assert sync_published(studio_env.releases_path, "TMR-099", {}, None) == []
    assert studio_env.releases_path.read_text() == before
