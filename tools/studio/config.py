"""config.py — paths used by tmr studio."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    web_root: Path
    assets_dir: Path
    scraper_dir: Path

    @property
    def releases_path(self) -> Path:
        return self.web_root / "data" / "releases.json"

    @property
    def tmr(self) -> Path:
        return self.web_root / "tools" / "tmr"


def load_config() -> Config:
    web_root = Path(__file__).resolve().parents[2]
    return Config(
        web_root=web_root,
        assets_dir=Path(os.environ.get("TMR_ASSETS_DIR", web_root.parent / "the-moon-assets")),
        scraper_dir=Path(os.environ.get(
            "TMR_SCRAPER_DIR", "/Users/tobe/Sites/logic-moon.de/dsp_scraper")),
    )
