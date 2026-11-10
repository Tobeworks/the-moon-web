import json

import pytest

from studio.folders import (classify, copy_files, create_release, next_catalog, slug,
                            write_meta)


def test_next_catalog(tmp_path):
    (tmp_path / "tmr-018-x-y").mkdir()
    assert next_catalog([{"catalog": "TMR-017"}], tmp_path) == "TMR-019"
    assert next_catalog([], tmp_path / "empty") == "TMR-001"


def test_create_release_makes_structure(tmp_path):
    d = create_release(tmp_path, "TMR-018", "Logic Moon", "Stellar Refuge", "2026-12-01")
    assert d.name == "tmr-018-logic-moon-stellar-refuge"
    assert (d / "audio").is_dir() and (d / "artwork").is_dir()
    r = json.loads((d / "release.json").read_text())
    assert r["catalog"] == "TMR-018" and r["artist"] == "Logic Moon"
    with pytest.raises(FileExistsError):
        create_release(tmp_path, "TMR-018", "Other", "Name")


def test_slug_strips_accents_and_symbols():
    assert slug("Réunion & Co.") == "reunion-co"


def test_classify():
    from pathlib import Path
    assert classify(Path("a.WAV")) == "audio" and classify(Path("c.jpg")) == "artwork"
    assert classify(Path("x.txt")) is None


@pytest.fixture
def rd(tmp_path):
    return create_release(tmp_path, "TMR-018", "A", "B")


def test_copy_sorts_audio_and_cover(rd, tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.wav").write_bytes(b"1")
    (src / "c.png").write_bytes(b"2")
    (src / "n.txt").write_bytes(b"3")
    res = copy_files(rd, [src / "a.wav", src / "c.png", src / "n.txt"])
    assert sorted(res["copied"]) == ["a.wav", "c.png"] and res["skipped"] == ["n.txt"]
    assert (rd / "audio" / "a.wav").exists() and (rd / "artwork" / "c.png").exists()


def test_copy_conflict_not_overwritten(rd, tmp_path):
    f = tmp_path / "a.wav"
    f.write_bytes(b"old")
    copy_files(rd, [f])
    f.write_bytes(b"new")
    res = copy_files(rd, [f])
    assert res["conflicts"] == ["a.wav"] and (rd / "audio" / "a.wav").read_bytes() == b"old"
    copy_files(rd, [f], overwrite=frozenset({"a.wav"}))
    assert (rd / "audio" / "a.wav").read_bytes() == b"new"


def test_copying_the_same_file_again_is_unchanged_not_a_conflict(rd, tmp_path):
    f = tmp_path / "a.wav"
    f.write_bytes(b"data")
    copy_files(rd, [f])
    again = copy_files(rd, [f])
    assert again["unchanged"] == ["a.wav"] and again["conflicts"] == [] and again["copied"] == []


def test_copy_folder_source(rd, tmp_path):
    src = tmp_path / "wavs"
    src.mkdir()
    (src / "1.wav").write_bytes(b"1")
    (src / "2.wav").write_bytes(b"2")
    assert sorted(copy_files(rd, [src])["copied"]) == ["1.wav", "2.wav"]


def test_write_meta_updates_and_rejects_unknown(rd):
    r = write_meta(rd, {"artist": "New", "bandcamp": "https://x.bandcamp.com/album/y"}, "# B\n\nText.")
    assert r["artist"] == "New" and r["platforms"]["bandcamp"].endswith("/y")
    assert (rd / "about.md").read_text() == "# B\n\nText."
    with pytest.raises(ValueError):
        write_meta(rd, {"tracks": []}, None)
    (rd / "release.json").unlink()
    with pytest.raises(ValueError):
        write_meta(rd, {"artist": "x"}, None)
