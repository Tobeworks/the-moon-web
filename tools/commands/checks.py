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


def publish_problems(release: dict, about: str = "") -> list[str]:
    """Reasons why a release must not be pushed. Only what the site cannot do without."""
    return [
        f"{field} is missing or still a placeholder"
        for field in ("artist", "title", "catalog")
        if is_placeholder(release.get(field))
    ]


def publish_warnings(release: dict, about: str) -> list[str]:
    """Things worth fixing that do not stop a push (it still goes through)."""
    warnings = []
    if is_placeholder(release.get("release_date")):
        warnings.append("release_date is missing — the release counts as released immediately")
    if is_placeholder((release.get("artwork") or {}).get("cover")):
        warnings.append("artwork.cover is not set")
    if about_is_placeholder(about):
        warnings.append("about.md is empty or still the placeholder — the release text will be blank")
    return warnings
