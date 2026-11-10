from studio.progress import progress

CONVERT = [
    "  →  Bitrate: 320k",
    "  →    Track 1 [320] — a.wav → 01_a.mp3",
    "  ✓    Track 1 [320] — 01_a.mp3 (9.4 MB)",
    "  ~    Track 2 [320] — 02_b.mp3 exists, skipping",
    "  ✗    Track 1 [128] — failed: boom",
]


def test_convert_counts_done_skipped_and_failed_tracks():
    assert progress("convert", CONVERT, 4) == {"done": 3, "total": 4, "pct": 75}


def test_push_counts_uploaded_files():
    lines = ["  →  01_a.mp3 (7000 KB) → /r/x", "  ✓  ✓ [128k] 01_a.mp3", "  ✓  ✓ cover_600.jpg"]
    assert progress("push", lines, 4) == {"done": 2, "total": 4, "pct": 50}


def test_other_jobs_and_unknown_total_have_no_progress():
    assert progress("validate", CONVERT, 4) is None
    assert progress("convert", CONVERT, None) is None
    assert progress("convert", CONVERT, 0) is None


def test_done_never_exceeds_total():
    assert progress("convert", CONVERT * 3, 4)["pct"] == 100
