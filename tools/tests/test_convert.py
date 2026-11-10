import io
import os
import shutil

import pytest
from mutagen.id3 import ID3
from PIL import Image

from commands.convert import convert_release, cover_for_id3, cover_is_newer


def test_cover_for_id3_is_small_jpeg(release_dir):
    data, mime = cover_for_id3(release_dir / "artwork")
    assert mime == "image/jpeg"
    assert max(Image.open(io.BytesIO(data)).size) <= 1500


def test_cover_for_id3_without_cover(release_dir):
    (release_dir / "artwork" / "cover.png").unlink()
    assert cover_for_id3(release_dir / "artwork") == (None, None)


def test_cover_is_newer_detects_changed_cover(release_dir):
    mp3 = release_dir / "x.mp3"
    mp3.write_bytes(b"x")
    cover = release_dir / "artwork" / "cover.png"
    os.utime(mp3, (1000, 1000))
    os.utime(cover, (2000, 2000))
    assert cover_is_newer(release_dir / "artwork", [mp3])
    os.utime(cover, (500, 500))
    assert not cover_is_newer(release_dir / "artwork", [mp3])


def test_no_tracks_is_an_error_not_a_silent_success(release_dir):
    import json
    p = release_dir / "release.json"
    data = json.loads(p.read_text())
    data["tracks"] = []
    p.write_text(json.dumps(data))
    with pytest.raises(SystemExit) as e:
        convert_release(str(release_dir))
    assert e.value.code == 1


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_renamed_track_replaces_the_old_mp3(release_dir):
    import json
    convert_release(str(release_dir))
    p = release_dir / "release.json"
    data = json.loads(p.read_text())
    data["tracks"][0]["title"] = "Fresh Name"
    p.write_text(json.dumps(data))
    convert_release(str(release_dir))
    for br in ("128", "320"):
        names = sorted(f.name for f in (release_dir / "export" / "mp3" / br).glob("*.mp3"))
        assert names == ["01_fresh_name.mp3"]


def test_missing_audio_file_gives_exit_code_1(release_dir):
    (release_dir / "audio" / "01_first.wav").unlink()
    with pytest.raises(SystemExit) as e:
        convert_release(str(release_dir))
    assert e.value.code == 1


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_convert_writes_both_bitrates_with_small_embedded_cover(release_dir):
    convert_release(str(release_dir))
    for br in ("128", "320"):
        mp3 = release_dir / "export" / "mp3" / br / "01_first.mp3"
        assert mp3.exists()
        apic = ID3(str(mp3)).getall("APIC")[0]
        assert apic.mime == "image/jpeg"
        assert max(Image.open(io.BytesIO(apic.data)).size) <= 1500
