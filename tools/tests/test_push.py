import json
import shutil
from pathlib import Path

import pytest

from commands.push import build_entry, build_platforms, upsert_release, write_releases

REPO_DATA = Path(__file__).parents[2] / "data"


def p(name, url):
    return {"name": name, "url": url}


def test_platforms_keep_links_added_after_release():
    existing = [p("bandcamp", "b"), p("spotify", "s"), p("amazon_music", "a"), p("deezer", "d")]
    out = build_platforms({"bandcamp": "b"}, existing)
    assert [x["name"] for x in out] == ["bandcamp", "spotify", "amazon_music", "deezer"]


def test_platforms_add_new_and_skip_empty():
    out = build_platforms({"bandcamp": "b", "soundcloud": "sc", "spotify": None, "deezer": ""}, [])
    assert out == [p("bandcamp", "b"), p("soundcloud", "sc")]


def test_platforms_existing_url_wins_and_empty_placeholder_is_replaced():
    existing = [p("spotify", "old"), p("deezer", "")]
    out = build_platforms({"spotify": "new", "deezer": "d"}, existing)
    assert out == [p("spotify", "old"), p("deezer", "d")]


def test_upsert_replaces_in_place_and_inserts_new_on_top():
    data = {"releases": [{"catalog": "TMR-3"}, {"catalog": "TMR-2"}, {"catalog": "TMR-1"}]}
    upsert_release(data, {"catalog": "TMR-2", "title": "new"})
    assert [r["catalog"] for r in data["releases"]] == ["TMR-3", "TMR-2", "TMR-1"]
    assert data["releases"][1]["title"] == "new"
    upsert_release(data, {"catalog": "TMR-4"})
    assert data["releases"][0]["catalog"] == "TMR-4"


RELEASE = {"artist": "A", "title": "T", "catalog": "TMR-9", "release_date": "2026-12-01",
           "format": "EP", "platforms": {"bandcamp": "b"},
           "tracks": [{"number": 1, "title": "One", "duration": "4:05"}]}


def entry(**kw):
    args = dict(release=RELEASE, about="text", cover="c", artwork={}, existing=None,
                urls={1: ("u128", "u320")})
    args.update(kw)
    return build_entry(**args)


def test_entry_runtime_falls_back_to_duration_and_year_from_date():
    e = entry()
    assert e["tracks"][0]["runtime"] == "4:05"
    assert e["tracks"][0]["url"] == "u128" and e["tracks"][0]["url_320"] == "u320"
    assert e["year"] == "2026"


def test_published_values_win_over_the_folder_and_the_folder_fills_gaps():
    existing = {"catalog": "TMR-9", "artist": "Published Artist", "title": "Published Title", "genre": "",
                "about": "Live text.", "release_date": "2026-01-01T00:00:00+00:00",
                "tracks": [{"number": 1, "title": "Hand Edited", "runtime": "9:99"}]}
    folder = {**RELEASE, "artist": "Folder Artist", "title": "FILL_IN", "genre": "Ambient",
              "release_date": "2099-01-01"}
    e = entry(release=folder, existing=existing, about="Folder text.")
    assert (e["artist"], e["title"]) == ("Published Artist", "Published Title")  # published wins
    assert e["genre"] == "Ambient"                                               # gap filled from the folder
    assert e["about"] == "Live text." and e["release_date"] == "2026-01-01"
    assert e["tracks"][0]["title"] == "Hand Edited" and e["tracks"][0]["runtime"] == "4:05"  # runtime from the files


def test_entry_keeps_manual_fields_and_dsp_links_of_existing_entry():
    existing = {"catalog": "TMR-9", "genre": "Dark Ambient", "year": "2025",
                "platforms": [p("spotify", "s")], "extra": 1}
    e = entry(existing=existing)
    assert e["genre"] == "Dark Ambient" and e["extra"] == 1
    assert [x["name"] for x in e["platforms"]] == ["spotify", "bandcamp"]


@pytest.fixture
def data_dir(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    shutil.copy(REPO_DATA / "releases.schema.json", d)
    shutil.copy(REPO_DATA / "releases.json", d)
    return d


def test_write_creates_backup_and_valid_file(data_dir):
    path = data_dir / "releases.json"
    data = json.loads(path.read_text())
    before = path.read_text()
    backup = write_releases(path, data)
    assert backup.read_text() == before
    assert backup.parent == data_dir / "backups"
    assert json.loads(path.read_text()) == data
    assert list(data_dir.glob("*.tmp")) == []


def test_write_refuses_schema_violation_and_leaves_file_untouched(data_dir):
    path = data_dir / "releases.json"
    before = path.read_text()
    data = json.loads(before)
    data["releases"][0]["platforms"] = "not a list"
    with pytest.raises(ValueError):
        write_releases(path, data)
    assert path.read_text() == before


# ── push_release: nothing may go out unless the release is complete ──────────

@pytest.fixture
def no_network(monkeypatch):
    import commands.push as push

    def boom(*a, **k):
        raise AssertionError("connected to the CDN although push should have stopped")

    monkeypatch.setattr(push, "sftp_connect", boom)
    monkeypatch.setattr(push, "ftp_connect", boom)
    monkeypatch.setattr(push, "load_env", lambda: {
        "CDN_HOST": "h", "CDN_USER": "u", "CDN_PUBLIC_URL": "https://cdn.example"})
    return push


def test_push_stops_before_upload_on_fill_in(release_dir, no_network):
    data = json.loads((release_dir / "release.json").read_text())
    data["artist"] = "FILL_IN"
    (release_dir / "release.json").write_text(json.dumps(data))
    with pytest.raises(SystemExit):
        no_network.push_release(str(release_dir))


def test_push_requires_public_url(release_dir, no_network, monkeypatch):
    monkeypatch.setattr(no_network, "load_env", lambda: {"CDN_HOST": "h", "CDN_USER": "u"})
    with pytest.raises(SystemExit):
        no_network.push_release(str(release_dir))


# ── a full push without any platform link must work (links come later) ───────

class FakeSftp:
    def __init__(self):
        self.uploaded = []

    def stat(self, path):
        raise FileNotFoundError(path)

    def mkdir(self, path):
        pass

    def put(self, local, remote):
        self.uploaded.append(remote)

    def close(self):
        pass


def run_push(release_dir, data_dir, monkeypatch, **release_changes):
    """Full push against a fake CDN; returns (saved entry, fake sftp)."""
    import commands.push as push

    (release_dir / "release.json").write_text(json.dumps({
        **json.loads((release_dir / "release.json").read_text()), **release_changes}))
    for br in ("128", "320"):
        d = release_dir / "export" / "mp3" / br
        d.mkdir(parents=True)
        (d / "01_first.mp3").write_bytes(b"x")
    sftp = FakeSftp()
    monkeypatch.setattr(push, "load_env", lambda: {
        "CDN_HOST": "h", "CDN_USER": "u", "CDN_PROTOCOL": "sftp", "CDN_PUBLIC_URL": "https://cdn.example"})
    monkeypatch.setattr(push, "sftp_connect", lambda env: (sftp, FakeSftp()))
    monkeypatch.setattr(push, "RELEASES_PATH", data_dir / "releases.json")
    push.push_release(str(release_dir))
    return json.loads((data_dir / "releases.json").read_text())["releases"][0], sftp


def test_push_without_text_or_date_goes_through_without_placeholders(release_dir, data_dir, monkeypatch):
    (release_dir / "about.md").write_text("# T\n\nWrite your release description here.\n")
    saved, _ = run_push(release_dir, data_dir, monkeypatch, release_date="YYYY-MM-DD", platforms={})
    assert saved["about"] == "" and "release_date" not in saved


def test_push_without_any_platform_url(release_dir, data_dir, monkeypatch):
    saved, sftp = run_push(release_dir, data_dir, monkeypatch, platforms={})
    assert saved["catalog"] == "TMR-099" and saved["platforms"] == []
    assert saved["tracks"][0]["url"].endswith("/128/01_first.mp3")
    assert len(sftp.uploaded) == 3  # 128k + 320k MP3 and the raw cover (no export/artwork)


def test_repush_of_a_live_release_keeps_its_data_even_if_the_folder_has_placeholders(release_dir, data_dir, monkeypatch):
    path = data_dir / "releases.json"
    data = json.loads(path.read_text())
    data["releases"].insert(0, {**data["releases"][0], "catalog": "TMR-099", "artist": "Live Artist",
                                "title": "Live Title", "about": "Live text.", "genre": "Drone",
                                "platforms": [{"name": "spotify", "url": "https://s"}]})
    path.write_text(json.dumps(data))
    (release_dir / "about.md").write_text("# T\n\nWrite your release description here.\n")
    saved, _ = run_push(release_dir, data_dir, monkeypatch, artist="FILL_IN", title="FILL_IN", release_date="YYYY-MM-DD")
    assert (saved["artist"], saved["title"], saved["about"], saved["genre"]) == ("Live Artist", "Live Title", "Live text.", "Drone")
    assert {"name": "spotify", "url": "https://s"} in saved["platforms"]
