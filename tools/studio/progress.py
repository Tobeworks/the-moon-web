"""
progress.py — progress of convert/push jobs, counted from the CLI's own output lines.
"""

import re

CONVERT_DONE = re.compile(r"Track \d+ \[(?:128|320)\] — .*(?:\(\d+(?:\.\d+)? MB\)| exists, skipping|failed:)")
PUSH_DONE = re.compile(r"✓\s+✓\s+\S")  # one line per uploaded file


def progress(kind: str | None, lines: list[str], total: int | None) -> dict | None:
    """{"done", "total", "pct"} for convert (one MP3 per track and bitrate) and push (one file
    per upload); None for other jobs or an unknown total."""
    pattern = {"convert": CONVERT_DONE, "push": PUSH_DONE}.get(kind or "")
    if not pattern or not total:
        return None
    done = min(total, sum(1 for line in lines if pattern.search(line)))
    return {"done": done, "total": total, "pct": round(done * 100 / total)}
