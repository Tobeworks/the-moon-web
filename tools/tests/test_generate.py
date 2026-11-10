import json

import pytest

from commands.checks import about_is_placeholder
from commands.generate import generate_release


def read(d):
    return json.loads((d / "release.json").read_text())


def test_fresh_folder_gets_tracks_with_duration_and_placeholder_about(release_dir):
    (release_dir / "release.json").unlink()
    (release_dir / "about.md").unlink()
    generate_release(str(release_dir))
    r = read(release_dir)
    assert r["catalog"] == "TMR-099"
    assert r["tracks"][0]["file"] == "01_first.wav" and r["tracks"][0]["duration"]
    assert about_is_placeholder((release_dir / "about.md").read_text())


def test_title_from_filename_has_no_underscores(release_dir):
    (release_dir / "audio" / "01_first.wav").rename(release_dir / "audio" / "Logic Moon - Drifter_Two.wav")
    (release_dir / "release.json").unlink()
    generate_release(str(release_dir))
    assert read(release_dir)["tracks"][0]["title"] == "Drifter Two"


def test_rerun_keeps_hand_edited_titles_and_extra_fields(release_dir):
    data = read(release_dir)
    data["tracks"][0]["title"] = "Handmade Title"
    data["year"], data["genre"] = "2026", "Dark Ambient"
    (release_dir / "release.json").write_text(json.dumps(data))
    generate_release(str(release_dir))
    r = read(release_dir)
    assert r["tracks"][0]["title"] == "Handmade Title"
    assert r["year"] == "2026" and r["genre"] == "Dark Ambient"


def test_unreadable_audio_aborts_without_touching_release_json(release_dir):
    before = (release_dir / "release.json").read_text()
    (release_dir / "audio" / "02_broken.wav").write_bytes(b"not audio")
    with pytest.raises(SystemExit) as e:
        generate_release(str(release_dir))
    assert e.value.code == 1
    assert (release_dir / "release.json").read_text() == before


def test_rerun_keeps_a_hand_set_track_order_and_appends_new_files(release_dir):
    import shutil
    audio = release_dir / "audio"
    shutil.copy(audio / "01_first.wav", audio / "02_second.wav")
    generate_release(str(release_dir))
    data = read(release_dir)
    data["tracks"].reverse()  # second before first
    (release_dir / "release.json").write_text(json.dumps(data))
    shutil.copy(audio / "01_first.wav", audio / "00_new.wav")
    generate_release(str(release_dir))
    assert [t["file"] for t in read(release_dir)["tracks"]] == ["02_second.wav", "01_first.wav", "00_new.wav"]
    assert [t["number"] for t in read(release_dir)["tracks"]] == [1, 2, 3]
