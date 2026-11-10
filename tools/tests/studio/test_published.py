import json

import pytest

from studio.published import update_entry, view

ENTRY = {
    "catalog": "TMR-099", "artist": "Logic Moon", "title": "Published", "format": "EP", "year": "2026",
    "genre": "Dark Ambient", "release_date": "2026-11-13T00:00:00+00:00", "about": "# Published\n\nLive text.",
    "platforms": [{"name": "spotify", "url": "https://s"}],
    "tracks": [{"number": 1, "title": "Pub One", "runtime": "7:12",
                "url": "https://cdn/x/audio/128/01_pub_one.mp3", "url_320": ""}],
}


def put_entry(cfg, **changes):
    data = json.loads(cfg.releases_path.read_text())
    base = data["releases"][0]
    data["releases"].insert(0, {**base, **ENTRY, **changes})
    cfg.releases_path.write_text(json.dumps(data))


def saved(cfg):
    return next(r for r in json.loads(cfg.releases_path.read_text())["releases"] if r["catalog"] == "TMR-099")


def test_view_of_a_published_release_comes_from_the_entry_not_the_folder(release_dir):
    v = view(release_dir, ENTRY)  # the folder says "Test Artist / Test Title", the entry is the truth
    r = v["release"]
    assert (r["artist"], r["title"], r["genre"], r["release_date"]) == ("Logic Moon", "Published", "Dark Ambient", "2026-11-13")
    assert v["about"] == ENTRY["about"] and r["platforms"] == {"bandcamp": ""}
    assert v["tracks"] == [{"number": 1, "title": "Pub One", "file": "01_first.wav", "duration": "7:12",
                            "mp3": "01_pub_one.mp3"}]


def test_view_of_an_unpublished_release_comes_from_the_folder(release_dir):
    v = view(release_dir, None)
    assert v["release"]["title"] == "Test Title" and v["tracks"][0]["mp3"] == "01_first.mp3"
    assert v["about"].startswith("# Test Title")


def test_view_without_folder(release_dir):
    v = view(None, ENTRY)
    assert v["tracks"][0]["file"] == "" and v["release"]["artist"] == "Logic Moon"


def test_update_writes_the_entry_and_reports_what_changed(studio_env):
    put_entry(studio_env)
    done = update_entry(studio_env.releases_path, "TMR-099", {
        "genre": "Ambient", "release_date": "2026-12-01", "bandcamp": "https://b",
        "track_titles": {"1": "New One"}, "title": "Published"}, "# P\n\nNew text.")
    e = saved(studio_env)
    assert e["genre"] == "Ambient" and e["release_date"] == "2026-12-01" and e["about"] == "# P\n\nNew text."
    assert e["tracks"][0]["title"] == "New One"
    assert e["platforms"] == [{"name": "spotify", "url": "https://s"}, {"name": "bandcamp", "url": "https://b"}]
    assert set(done) == {"genre", "release_date", "bandcamp", "track_titles", "about"}  # title unchanged


def test_update_can_clear_optional_fields_and_remove_bandcamp(studio_env):
    put_entry(studio_env, platforms=[{"name": "bandcamp", "url": "https://old"}])
    update_entry(studio_env.releases_path, "TMR-099", {"genre": "", "bandcamp": ""}, "")
    e = saved(studio_env)
    assert e["genre"] == "" and e["about"] == "" and e["platforms"] == []


def test_update_never_writes_placeholders_into_required_fields(studio_env):
    put_entry(studio_env)
    assert update_entry(studio_env.releases_path, "TMR-099",
                        {"artist": "FILL_IN", "title": "", "release_date": "YYYY-MM-DD"}, None) == []
    e = saved(studio_env)
    assert (e["artist"], e["title"]) == ("Logic Moon", "Published")


def test_placeholder_text_is_stored_as_empty_text(studio_env):
    put_entry(studio_env)
    update_entry(studio_env.releases_path, "TMR-099", {}, "# T\n\nWrite your release description here.\n")
    assert saved(studio_env)["about"] == ""


def test_unknown_release_and_no_change_write_nothing(studio_env):
    before = studio_env.releases_path.read_text()
    with pytest.raises(KeyError):
        update_entry(studio_env.releases_path, "TMR-500", {"genre": "x"}, None)
    put_entry(studio_env)
    after_put = studio_env.releases_path.read_text()
    assert update_entry(studio_env.releases_path, "TMR-099", {"genre": "Dark Ambient"}, None) == []
    assert studio_env.releases_path.read_text() == after_put and before != after_put
