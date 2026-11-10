from commands.checks import about_is_placeholder, is_placeholder, publish_problems

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


def test_publish_problems_lists_everything_wrong():
    bad = {**OK, "artist": "FILL_IN", "release_date": "YYYY-MM-DD",
           "artwork": {"cover": "FILL_IN"}}
    problems = publish_problems(bad, "# T\n\nWrite your release description here.\n")
    assert len(problems) == 4
