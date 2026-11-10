"""
gitops.py — the one git write the studio does: commit data/releases.json (local only, no push).
"""

import subprocess

from studio.config import Config

PATH = "data/releases.json"


def _git(cfg: Config, *args: str) -> str:
    res = subprocess.run(["git", "-C", str(cfg.web_root), *args], capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        raise RuntimeError((res.stderr or res.stdout).strip()[-400:] or "git failed")
    return res.stdout


def releases_dirty(cfg: Config) -> bool:
    try:
        return bool(_git(cfg, "status", "--porcelain", "--", PATH).strip())
    except (RuntimeError, OSError, subprocess.SubprocessError):
        return False


def commit_releases(cfg: Config, message: str) -> str:
    """Commit only data/releases.json (other staged files stay staged). Returns the short hash."""
    message = message.strip()
    if not message:
        raise ValueError("commit message is empty")
    if not releases_dirty(cfg):
        raise ValueError("data/releases.json has no changes")
    _git(cfg, "commit", "-m", message, "--", PATH)
    return _git(cfg, "rev-parse", "--short", "HEAD").strip()
