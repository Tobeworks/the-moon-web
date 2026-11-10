import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))  # tools/ → `import commands.*`


@pytest.fixture
def release_dir(tmp_path):
    """A minimal, valid asset folder: audio/, artwork/, release.json, about.md."""
    import soundfile as sf
    from PIL import Image

    d = tmp_path / "tmr-099-test-artist-test-title"
    (d / "audio").mkdir(parents=True)
    (d / "artwork").mkdir()
    sf.write(str(d / "audio" / "01_first.wav"), [0.0] * 4800, 48000)
    Image.new("RGB", (3000, 3000), "gray").save(d / "artwork" / "cover.png")
    release = {
        "release_id": "TMR-099", "artist": "Test Artist", "title": "Test Title",
        "format": "EP", "label": "The Moon Records", "catalog": "TMR-099",
        "release_date": "2026-12-01",
        "tracks": [{"number": 1, "title": "First", "file": "01_first.wav", "duration": "0:00"}],
        "artwork": {"cover": "cover.png"},
        "platforms": {"bandcamp": "https://x.bandcamp.com/album/t"},
    }
    (d / "release.json").write_text(json.dumps(release))
    (d / "about.md").write_text("# Test Title\n\nA real description of the release.\n")
    return d


@pytest.fixture
def studio_env(tmp_path):
    """Temp web root (data/releases.json + schema + .env) and assets dir."""
    import shutil

    from studio.config import Config

    web = tmp_path / "web"
    (web / "data").mkdir(parents=True)
    repo_data = Path(__file__).parents[2] / "data"
    shutil.copy(repo_data / "releases.schema.json", web / "data")
    shutil.copy(repo_data / "releases.json", web / "data")
    (web / ".env").write_text("CDN_HOST=h\nCDN_USER=u\nCDN_PASSWORD=secret-pw\nCDN_PUBLIC_URL=https://cdn.example\n")
    assets = tmp_path / "assets"
    assets.mkdir()
    return Config(web_root=web, assets_dir=assets, scraper_dir=tmp_path / "scraper")
