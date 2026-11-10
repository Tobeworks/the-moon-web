import json

import pytest
from PIL import Image

from commands.validate import validate_release


def edit_release(d, **changes):
    p = d / "release.json"
    data = json.loads(p.read_text())
    data.update(changes)
    p.write_text(json.dumps(data))


def test_valid_release_passes(release_dir):
    validate_release(str(release_dir))


@pytest.mark.parametrize("field", ["artist", "title"])
def test_fill_in_placeholder_is_rejected(release_dir, field):
    edit_release(release_dir, **{field: "FILL_IN"})
    with pytest.raises(SystemExit) as e:
        validate_release(str(release_dir))
    assert e.value.code == 1


def test_placeholder_cover_name_is_rejected(release_dir):
    edit_release(release_dir, artwork={"cover": "FILL_IN"})
    with pytest.raises(SystemExit):
        validate_release(str(release_dir))


def test_placeholder_about_is_rejected(release_dir):
    (release_dir / "about.md").write_text("# T\n\nWrite your release description here.\n")
    with pytest.raises(SystemExit):
        validate_release(str(release_dir))


def test_missing_about_is_rejected(release_dir):
    (release_dir / "about.md").unlink()
    with pytest.raises(SystemExit):
        validate_release(str(release_dir))


def test_jpg_cover_is_accepted(release_dir):
    (release_dir / "artwork" / "cover.png").unlink()
    Image.new("RGB", (3000, 3000), "gray").save(release_dir / "artwork" / "cover.jpg")
    validate_release(str(release_dir))


def test_small_cover_is_rejected(release_dir):
    Image.new("RGB", (1000, 1000), "gray").save(release_dir / "artwork" / "cover.png")
    with pytest.raises(SystemExit):
        validate_release(str(release_dir))
