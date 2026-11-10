"""
push.py — The Moon Records CDN uploader
Uploads MP3s (128k + 320k) + processed artwork to cdn.the-moon-records.de via FTP/SFTP.
Updates data/releases.json in the OS repo.

Input:  release.json + export/mp3/128/ + export/mp3/320/ + export/artwork/
Output: CDN upload + data/releases.json updated
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from colorama import init, Fore, Style

init(autoreset=True)


def ok(msg):
    print(f"  {Fore.GREEN}✓{Style.RESET_ALL}  {msg}")


def info(msg):
    print(f"  {Fore.CYAN}→{Style.RESET_ALL}  {msg}")


def warn(msg):
    print(f"  {Fore.YELLOW}~{Style.RESET_ALL}  {msg}")


def fail(msg):
    print(f"  {Fore.RED}✗{Style.RESET_ALL}  {msg}")


def header(msg):
    print(f"\n{Fore.WHITE}{Style.BRIGHT}{msg}{Style.RESET_ALL}")
    print("─" * 50)


def load_env() -> dict:
    """Load .env from OS repo root."""
    env_path = Path(__file__).parents[2] / ".env"
    if not env_path.exists():
        fail(f".env not found at {env_path}")
        fail("Copy .env.example to .env and fill in credentials.")
        sys.exit(1)

    env = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        env[key.strip()] = val.strip()
    return env


def ftp_connect(env: dict):
    """Return an open FTP or FTPS client."""
    import ftplib

    host = env["CDN_HOST"]
    port = int(env.get("CDN_PORT", 21))
    user = env["CDN_USER"]
    password = env.get("CDN_PASSWORD", "")
    protocol = env.get("CDN_PROTOCOL", "ftp").lower()

    if protocol == "ftps":
        ftp = ftplib.FTP_TLS()
        info("Protocol: FTPS (explicit TLS)")
    else:
        ftp = ftplib.FTP()
        info("Protocol: FTP")

    ftp.connect(host, port, timeout=10)
    ftp.login(user, password)

    if protocol == "ftps":
        ftp.prot_p()

    return ftp


def sftp_connect(env: dict):
    """Return an open paramiko SFTP client. Supports key and password auth."""
    try:
        import paramiko
    except ImportError:
        fail("paramiko not installed — run: pip install paramiko")
        sys.exit(1)

    key_path = env.get("CDN_KEY_PATH", "")
    password = env.get("CDN_PASSWORD", "")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs = dict(
        hostname=env["CDN_HOST"],
        port=int(env.get("CDN_PORT", 22)),
        username=env["CDN_USER"],
    )

    if key_path:
        key_path = os.path.expanduser(key_path)
        connect_kwargs["key_filename"] = key_path
        info(f"Auth: public key ({key_path})")
    elif password:
        connect_kwargs["password"] = password
        info("Auth: password")
    else:
        info("Auth: SSH agent / default keys")

    ssh.connect(**connect_kwargs)
    return ssh.open_sftp(), ssh


def get_protocol(env: dict) -> str:
    return env.get("CDN_PROTOCOL", "sftp").lower()


def ftp_makedirs(ftp, remote_path: str):
    """Recursively create remote directories via FTP."""
    parts = [p for p in remote_path.split("/") if p]
    current = ""
    for part in parts:
        current = f"{current}/{part}"
        try:
            ftp.cwd(current)
        except Exception:
            ftp.mkd(current)


def sftp_makedirs(sftp, remote_path: str):
    """Recursively create remote directories via SFTP."""
    parts = remote_path.split("/")
    current = ""
    for part in parts:
        if not part:
            continue
        current = f"{current}/{part}"
        try:
            sftp.stat(current)
        except FileNotFoundError:
            sftp.mkdir(current)


def makedirs(client, remote_path: str, client_type: str):
    if client_type == "sftp":
        sftp_makedirs(client, remote_path)
    else:
        ftp_makedirs(client, remote_path)


def upload_file(client, local: Path, remote: str, client_type: str):
    """Upload a single file via FTP or SFTP."""
    size_kb = local.stat().st_size // 1024
    info(f"  {local.name} ({size_kb} KB) → {remote}")
    if client_type == "sftp":
        client.put(str(local), remote)
    else:
        with open(local, "rb") as f:
            client.storbinary(f"STOR {remote}", f)


def test_connection():
    """Test FTP/SFTP connection and permissions — no upload."""
    print(
        f"\n{Fore.RED}{Style.BRIGHT}THE MOON RECORDS — CONNECTION TEST{Style.RESET_ALL}\n"
    )

    header("1. CREDENTIALS")
    env = load_env()
    protocol = get_protocol(env)
    cdn_base = env.get("CDN_BASE_PATH", "/releases")
    ok(f"Protocol: {protocol.upper()}")
    ok(f"Host:     {env['CDN_HOST']}")
    ok(f"Port:     {env.get('CDN_PORT', 21 if protocol != 'sftp' else 22)}")
    ok(f"User:     {env['CDN_USER']}")
    ok(f"Base:     {cdn_base}")

    header("2. CONNECTING")
    try:
        if protocol == "sftp":
            client, ssh = sftp_connect(env)
            client_type = "sftp"
        else:
            client = ftp_connect(env)
            client_type = "ftp"
            ssh = None
        ok("Connected successfully")
    except Exception as e:
        fail(f"Connection failed: {e}")
        sys.exit(1)

    header("3. PERMISSIONS")
    import io

    test_file = f"{cdn_base}/.pg-test"

    try:
        if client_type == "sftp":
            try:
                client.stat(cdn_base)
                ok(f"Base path exists: {cdn_base}")
            except FileNotFoundError:
                warn(f"Base path not found: {cdn_base} — will be created on push")
            client.putfo(io.BytesIO(b"the-moon-test"), test_file)
            client.remove(test_file)
            entries = client.listdir(cdn_base)
        else:
            try:
                client.cwd(cdn_base)
                ok(f"Base path exists: {cdn_base}")
            except Exception:
                warn(f"Base path not found: {cdn_base} — will be created on push")
                client.cwd("/")
            client.storbinary(f"STOR {test_file}", io.BytesIO(b"the-moon-test"))
            client.delete(test_file)
            entries = client.nlst(cdn_base)

        ok("Write + delete permissions OK")
        ok(f"Directory listing OK — {len(entries)} item(s)")
        for e in entries[:5]:
            info(f"  {e}")
        if len(entries) > 5:
            info(f"  ... and {len(entries) - 5} more")

    except Exception as e:
        fail(f"Permission test failed: {e}")
        if client_type == "sftp":
            client.close()
            ssh.close()
        else:
            client.quit()
        sys.exit(1)

    if client_type == "sftp":
        client.close()
        ssh.close()
    else:
        client.quit()

    header("RESULT")
    ok(f"{protocol.upper()} connection fully operational")
    print()


def push_release(release_path: str, preview_only: bool = False):
    path = Path(release_path)

    print(f"\n{Fore.RED}{Style.BRIGHT}THE MOON RECORDS — CDN PUSH{Style.RESET_ALL}")
    print(f"Release: {path.name}\n")

    # ── Load credentials ───────────────────────────────────────────────────────
    header("1. CREDENTIALS")
    env = load_env()
    cdn_base = env.get("CDN_BASE_PATH", "/releases")
    cdn_public = env.get("CDN_PUBLIC_URL")
    ok(f"CDN: {env['CDN_HOST']}")

    # ── Load release.json ──────────────────────────────────────────────────────
    header("2. RELEASE DATA")
    json_path = path / "release.json"
    if not json_path.exists():
        fail("release.json not found — run ./pg generate first")
        sys.exit(1)

    with open(json_path) as f:
        data = json.load(f)

    catalog = data.get("catalog", path.name)
    artist = data.get("artist", "")
    title = data.get("title", "")
    ok(f"{catalog} — {artist} — {title}")

    # ── Resolve audio files ────────────────────────────────────────────────────
    header("3. ASSETS")
    slug = path.name

    # Audio — prefer preview if --preview-only, else use 128k + 320k
    preview_dir = path / "export" / "preview"
    mp3_128_dir = path / "export" / "mp3" / "128"
    mp3_320_dir = path / "export" / "mp3" / "320"
    # Legacy fallback: export/mp3/ (flat, old convert output)
    mp3_legacy_dir = path / "export" / "mp3"

    if preview_only:
        preview_files = (
            sorted(preview_dir.glob("*.mp3")) if preview_dir.exists() else []
        )
        if not preview_files:
            fail("No preview clips found — run ./pg convert --preview first")
            sys.exit(1)
        audio_plan = [("preview", preview_dir, preview_files)]
        info(f"Mode: preview-only ({len(preview_files)} clip(s))")
    else:
        audio_plan = []
        for label, d in [("128", mp3_128_dir), ("320", mp3_320_dir)]:
            files = sorted(d.glob("*.mp3")) if d.exists() else []
            # fallback: legacy flat mp3 dir
            if not files and label == "320" and mp3_legacy_dir.exists():
                legacy_files = [
                    f
                    for f in sorted(mp3_legacy_dir.glob("*.mp3"))
                    if f.parent == mp3_legacy_dir
                ]
                if legacy_files:
                    warn(
                        f"No export/mp3/320/ found — using legacy export/mp3/ for 320k"
                    )
                    files = legacy_files
            audio_plan.append((label, d, files))

        total_audio = sum(len(f) for _, _, f in audio_plan)
        if total_audio == 0:
            fail("No MP3s found — run ./pg convert first")
            sys.exit(1)
        for label, _, files in audio_plan:
            ok(f"{len(files)} audio file(s) [{label}kbps]")

    # Artwork — processed variants preferred, fallback to raw artwork/
    artwork_export_dir = path / "export" / "artwork"
    raw_artwork_dir = path / "artwork"

    artwork_variants = []
    if artwork_export_dir.exists():
        artwork_variants = sorted(artwork_export_dir.glob("*.jpg")) + sorted(
            artwork_export_dir.glob("*.webp")
        )
        ok(f"{len(artwork_variants)} artwork variant(s) (processed)")
    else:
        # fallback: upload raw artwork
        raw_covers = (
            (
                sorted(raw_artwork_dir.glob("*.jpg"))
                + sorted(raw_artwork_dir.glob("*.png"))
            )
            if raw_artwork_dir.exists()
            else []
        )
        artwork_variants = raw_covers
        if raw_covers:
            warn(
                f"{len(raw_covers)} raw artwork file(s) — run ./pg convert first for optimised variants"
            )
        else:
            warn("No artwork found")

    # ── Connect ────────────────────────────────────────────────────────────────
    header("4. CONNECTING")
    protocol = get_protocol(env)
    client_type = "sftp" if protocol == "sftp" else "ftp"
    ssh = None

    try:
        if client_type == "sftp":
            client, ssh = sftp_connect(env)
        else:
            client = ftp_connect(env)
        ok(f"Connected via {protocol.upper()} to {env['CDN_HOST']}")
    except Exception as e:
        fail(f"Connection failed: {e}")
        sys.exit(1)

    # ── Upload audio ───────────────────────────────────────────────────────────
    header("5. UPLOADING AUDIO")
    remote_base = f"{cdn_base}/{slug}"

    # Map: bitrate_label → {filename: remote_url}
    cdn_audio_map = {}  # e.g. {'128': {'01_...mp3': 'https://...'}, '320': {...}}

    for label, local_dir, files in audio_plan:
        remote_dir = f"{remote_base}/audio/{label}"
        makedirs(client, remote_dir, client_type)
        cdn_audio_map[label] = {}
        for mp3 in files:
            remote_path = f"{remote_dir}/{mp3.name}"
            upload_file(client, mp3, remote_path, client_type)
            cdn_audio_map[label][mp3.name] = (
                f"{cdn_public}/releases/{slug}/audio/{label}/{mp3.name}"
            )
            ok(f"✓ [{label}k] {mp3.name}")

    # ── Upload artwork ─────────────────────────────────────────────────────────
    header("6. UPLOADING ARTWORK")
    remote_art = f"{remote_base}/artwork"
    makedirs(client, remote_art, client_type)

    for art in artwork_variants:
        remote_path = f"{remote_art}/{art.name}"
        upload_file(client, art, remote_path, client_type)
        ok(f"✓ {art.name}")

    if client_type == "sftp":
        client.close()
        ssh.close()
    else:
        client.quit()

    # ── Build artwork index for releases.json ──────────────────────────────────
    # cover = 600px JPG (primary for web)
    art_base_url = f"{cdn_public}/releases/{slug}/artwork"
    cdn_cover = None
    cdn_artwork = {}  # e.g. {'600': {'jpg': '...', 'webp': '...'}}

    for art in artwork_variants:
        name = art.name  # e.g. cover_600.jpg
        url = f"{art_base_url}/{name}"
        # Parse size from filename: cover_<size>.jpg / cover_<size>.webp
        import re

        m = re.match(r"cover_(\d+)\.(jpg|webp)", name)
        if m:
            sz, fmt = m.group(1), m.group(2)
            if sz not in cdn_artwork:
                cdn_artwork[sz] = {}
            cdn_artwork[sz][fmt] = url
            if sz == "600" and fmt == "jpg":
                cdn_cover = url
        else:
            # Raw artwork fallback (no size in name)
            cdn_cover = url

    # ── Update data/releases.json ──────────────────────────────────────────────
    header("7. UPDATING releases.json")
    repo_root = Path(__file__).parents[2]
    releases_path = repo_root / "data" / "releases.json"

    with open(releases_path) as f:
        releases_data = json.load(f)

    # Build track list — merge release.json metadata with CDN URLs
    release_tracks = data.get("tracks", [])

    # Determine track file list from 128k (primary for web) or preview
    primary_label = "preview" if preview_only else "128"
    primary_audio = cdn_audio_map.get(primary_label, {})
    secondary_audio = cdn_audio_map.get("320", {})

    # Build filename→url maps
    def build_filename_map(label_map: dict) -> dict:
        """Return {track_number_prefix: url} for matching by track number."""
        return {name: url for name, url in label_map.items()}

    primary_by_name = build_filename_map(primary_audio)
    secondary_by_name = build_filename_map(secondary_audio)

    def find_url(url_map: dict, track_num: int) -> str:
        """Match by track number prefix (e.g. '01_')."""
        prefix = str(track_num).zfill(2) + "_"
        for name, url in url_map.items():
            if name.startswith(prefix):
                return url
        return ""

    tracks_out = []
    for i, t in enumerate(release_tracks):
        num = t.get("number", i + 1)
        tracks_out.append(
            {
                "number": num,
                "title": t.get("title", ""),
                "runtime": t.get("runtime", ""),
                "url": find_url(primary_audio, num),  # 128k for web player
                "url_320": find_url(secondary_audio, num),  # 320k for download
            }
        )

    # Build platforms array per schema
    # Supports both nested "platforms" object and legacy flat "bandcamp_url"
    platforms = []
    platforms_data = data.get("platforms", data.get("plaforms", {})) or {}
    platform_names = ["bandcamp", "spotify", "soundcloud", "apple_music", "beatport"]
    for name in platform_names:
        url = platforms_data.get(name)
        if url:
            platforms.append({"name": name, "url": url})
    # legacy flat field fallback
    bandcamp_url = data.get("bandcamp_url", "")
    if bandcamp_url and not any(p["name"] == "bandcamp" for p in platforms):
        platforms.append({"name": "bandcamp", "url": bandcamp_url})

    about_path = path / "about.md"
    about = about_path.read_text(encoding="utf-8").strip() if about_path.exists() else ""
    if about:
        ok("about.md loaded")
    else:
        warn("about.md not found or empty — 'about' will be blank")

    entry = {
        "catalog": catalog,
        "artist": artist,
        "title": title,
        "format": data.get("format", ""),
        "year": data.get("year", ""),
        "genre": data.get("genre", ""),
        "about": about,
        "cover": cdn_cover,
        "artwork": cdn_artwork,
        "platforms": platforms,
        "tracks": tracks_out,
        "pushed_at": datetime.now(timezone.utc).isoformat(),
    }

    # Only include release_date if present and non-empty
    release_date = data.get("release_date", "")
    if release_date:
        entry["release_date"] = release_date

    existing = [r for r in releases_data["releases"] if r["catalog"] != catalog]
    releases_data["releases"] = [entry] + existing
    releases_data["_meta"]["generated"] = datetime.now(timezone.utc).isoformat()

    with open(releases_path, "w") as f:
        json.dump(releases_data, f, indent=2)

    ok(f"releases.json updated — {len(releases_data['releases'])} release(s)")

    header("8. DONE")
    ok(f"CDN: {cdn_public}/releases/{slug}/")
    info("Next: commit data/releases.json, then push OS repo")
    print()
