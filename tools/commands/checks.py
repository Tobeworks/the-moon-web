"""
checks.py — shared checks used by generate, validate and push.

Keeps the definition of "still a placeholder" in one place.
"""

PLACEHOLDERS = {"FILL_IN", "YYYY-MM-DD"}
ABOUT_PLACEHOLDER = "Write your release description here."

# Platform names are coupled to the logo files in the-moon-web/src/assets/dsp/.
PLATFORM_NAMES = [
    "bandcamp",
    "spotify",
    "apple_music",
    "amazon_music",
    "soundcloud",
    "deezer",
    "beatport",
]


def is_placeholder(value) -> bool:
    return value is None or str(value).strip() in ("", *PLACEHOLDERS)


def about_is_placeholder(text: str) -> bool:
    """True if about.md is empty, still the generator's text, or only a heading."""
    text = (text or "").strip()
    if not text or ABOUT_PLACEHOLDER in text:
        return True
    return all(line.startswith("#") or not line.strip() for line in text.splitlines())


def publish_problems(release: dict, about: str) -> list[str]:
    """Reasons why a release must not be pushed yet. Empty list = fine."""
    problems = [
        f"{field} is missing or still a placeholder"
        for field in ("artist", "title", "catalog", "release_date")
        if is_placeholder(release.get(field))
    ]
    if is_placeholder((release.get("artwork") or {}).get("cover")):
        problems.append("artwork.cover is missing or still a placeholder")
    if about_is_placeholder(about):
        problems.append("about.md is missing or still the placeholder text")
    return problems
