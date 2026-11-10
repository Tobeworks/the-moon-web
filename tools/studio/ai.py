"""
ai.py — draft the release text (about.md) with the Anthropic API.

Access: ANTHROPIC_API_KEY (environment or .env in the repo root), optional ANTHROPIC_MODEL.
Sent to the API: artist, title, format, genre, date, track names and durations, the author's
keywords, the current draft and up to three older release texts as style reference.
"""

import os

from studio.config import Config

MODEL = "claude-sonnet-5-5"

SYSTEM = """You write release texts for The Moon Records, an independent ambient label.

Voice: calm, concrete, atmospheric, a little literary. Never hype.
Output: only the text itself. No heading, no title line, no markdown, no quotation marks around it.
Length: 2 to 4 short paragraphs, 90 to 170 words in total. English.
Mention the release title and the track names where it reads naturally.
Use only the facts you are given. Do not invent collaborators, instruments, places, earlier releases,
labels or release details that are not in the input.
No emojis, no hashtags, no calls to action, no clichés such as "sonic journey", "tapestry" or "immersive soundscape"."""


class AiError(Exception):
    pass


def _env(cfg: Config) -> dict:
    """ANTHROPIC_* from the environment, falling back to .env in the repo root."""
    values = {}
    path = cfg.web_root / ".env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.strip().partition("=")
            if sep and key.startswith("ANTHROPIC_") and not line.lstrip().startswith("#"):
                values[key] = value.split(" #", 1)[0].strip().strip("\"'")
    for key in ("ANTHROPIC_API_KEY", "ANTHROPIC_MODEL"):
        if os.environ.get(key):
            values[key] = os.environ[key]
    return values


def ready(cfg: Config) -> bool:
    return bool(_env(cfg).get("ANTHROPIC_API_KEY"))


def build_prompt(release: dict, notes: str, draft: str, examples: list[str]) -> str:
    tracks = "\n".join(f"{t.get('number', i)}. {t.get('title', '')} ({t.get('duration') or t.get('runtime') or '?'})"
                       for i, t in enumerate(release.get("tracks") or [], 1))
    parts = [
        f"Artist: {release.get('artist', '')}",
        f"Title: {release.get('title', '')}",
        f"Format: {release.get('format', '')}",
        f"Genre: {release.get('genre') or 'not set'}",
        f"Release date: {release.get('release_date', '')}",
        f"Tracks:\n{tracks}",
    ]
    if notes.strip():
        parts.append(f"The author's keywords and background (use these, stay within them):\n{notes.strip()}")
    if draft.strip():
        parts.append(f"Current draft to improve (keep what works):\n{draft.strip()}")
    if examples:
        parts.append("Older release texts of the label, for voice and length only. Do not reuse their sentences:\n\n"
                     + "\n\n---\n\n".join(examples))
    parts.append("Write the release text now.")
    return "\n\n".join(parts)


def generate_about(cfg: Config, release: dict, notes: str = "", draft: str = "",
                   examples: list[str] | None = None, client=None) -> str:
    env = _env(cfg)
    if client is None:
        if not env.get("ANTHROPIC_API_KEY"):
            raise AiError("ANTHROPIC_API_KEY fehlt in der .env im Repo-Root.")
        try:
            import anthropic
        except ImportError:
            raise AiError("Das Paket 'anthropic' fehlt. Installieren: pip install -r tools/requirements.txt")
        client = anthropic.Anthropic(api_key=env["ANTHROPIC_API_KEY"], timeout=120.0)
    try:
        import anthropic
        res = client.messages.create(
            model=env.get("ANTHROPIC_MODEL") or MODEL, max_tokens=1500, system=SYSTEM,
            messages=[{"role": "user", "content": build_prompt(release, notes, draft, examples or [])}])
    except anthropic.AuthenticationError:
        raise AiError("Die KI hat den Zugang abgelehnt. ANTHROPIC_API_KEY in der .env prüfen.")
    except anthropic.RateLimitError:
        raise AiError("Die KI ist gerade überlastet (Ratenbegrenzung). Gleich noch einmal versuchen.")
    except anthropic.APIConnectionError:
        raise AiError("Keine Verbindung zur KI. Internetverbindung prüfen.")
    except anthropic.APIStatusError as e:
        raise AiError(f"Die KI meldet einen Fehler ({e.status_code}): {e.message}")
    if res.stop_reason == "refusal":
        raise AiError("Die KI hat die Anfrage abgelehnt. Stichworte anders formulieren.")
    text = "".join(b.text for b in res.content if b.type == "text").strip()
    if not text:
        raise AiError("Die KI hat keinen Text geliefert. Bitte noch einmal versuchen.")
    return text
