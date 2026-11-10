"""
frontend_build.py — builds the Vue UI (studio/frontend → studio/dist) when it is missing or older than its sources.
"""

import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
FRONTEND = HERE / "frontend"
DIST = HERE / "dist"


def needs_build(frontend: Path = FRONTEND, dist: Path = DIST) -> bool:
    built = dist / "index.html"
    if not built.is_file():
        return True
    sources = [f for f in [*(frontend / "src").rglob("*"), frontend / "index.html", frontend / "package.json",
                           frontend / "vite.config.ts"] if f.is_file()]
    return any(f.stat().st_mtime > built.stat().st_mtime for f in sources)


def build(frontend: Path = FRONTEND) -> None:
    """Raises RuntimeError with a readable message when pnpm is missing or the build fails."""
    pnpm = shutil.which("pnpm")
    if pnpm is None:
        raise RuntimeError("pnpm fehlt: die Oberfläche muss gebaut werden (pnpm install && pnpm build in tools/studio/frontend)")
    try:
        if not (frontend / "node_modules").exists():
            subprocess.run([pnpm, "install", "--frozen-lockfile"], cwd=frontend, check=True)
        subprocess.run([pnpm, "build"], cwd=frontend, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Bauen der Oberfläche fehlgeschlagen ({' '.join(map(str, e.cmd))})") from e
