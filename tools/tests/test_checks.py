from commands.checks import about_is_placeholder, is_placeholder, publish_problems, publish_warnings

OK = {"artist": "A", "title": "T", "catalog": "TMR-1", "release_date": "2026-01-01",
      "artwork": {"cover": "c.png"}}


def test_placeholders():
    assert is_placeholder("FILL_IN") and is_placeholder("YYYY-MM-DD")
    assert is_placeholder("") and is_placeholder(None) and is_placeholder("  ")
    assert not is_placeholder("Logic Moon")


def test_about_placeholder_variants():
    assert about_is_placeholder("")
    assert about_is_placeholder("# Title\n\nWrite your release description here.\n")
    assert about_is_placeholder("# Only a heading\n")
    assert not about_is_placeholder("# Title\n\nReal text.\n")


def test_publish_problems_clean():
    assert publish_problems(OK, "# T\n\nReal text.") == []


def test_only_artist_title_catalog_block_a_push():
    bad = {**OK, "artist": "FILL_IN", "title": "", "catalog": None}
    assert len(publish_problems(bad, "")) == 3
    soft = {**OK, "release_date": "YYYY-MM-DD", "artwork": {"cover": "FILL_IN"}}
    assert publish_problems(soft, "# T\n\nWrite your release description here.\n") == []


def test_missing_text_date_and_cover_are_warnings_only():
    soft = {**OK, "release_date": "YYYY-MM-DD", "artwork": {"cover": "FILL_IN"}}
    assert len(publish_warnings(soft, "# T\n\nWrite your release description here.\n")) == 3
    assert publish_warnings(OK, "# T\n\nReal text.") == []
