"""
push.py — The Moon Records CDN uploader
Uploads MP3s (128k + 320k) + processed artwork to cdn.the-moon-records.de via FTP/SFTP.
Updates data/releases.json in the OS repo.

Input:  release.json + export/mp3/128/ + export/mp3/320/ + export/artwork/
Output: CDN upload + data/releases.json updated
"""

import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from colorama import init, Fore, Style

from commands.checks import PLATFORM_NAMES, publish_problems

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

    missing = [k for k in ("CDN_HOST", "CDN_USER") if not env.get(k)]
    if missing:
        fail(f"{', '.join(missing)} missing in {env_path}")
        fail("Add the CDN_* credentials (see AGENTS.md / old OS repo .env).")
        sys.exit(1)
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


RELEASES_PATH = Path(__file__).parents[2] / "data" / "releases.json"


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


def build_platforms(release_platforms: dict, existing: list) -> list:
    """Merge platform links. Links already in releases.json (e.g. DSP links added
    after the release) are kept; release.json only adds missing, non-empty ones."""
    out = [dict(p) for p in existing if p.get("url")]
    have = {p["name"] for p in out}
    for name in PLATFORM_NAMES:
        url = (release_platforms or {}).get(name)
        if url and name not in have:
            out.append({"name": name, "url": url})
    return out


def upsert_release(data: dict, entry: dict) -> None:
    """Replace the entry with the same catalog in place, or insert a new one on top."""
    for i, r in enumerate(data["releases"]):
        if r["catalog"] == entry["catalog"]:
            data["releases"][i] = entry
            return
    data["releases"].insert(0, entry)


def build_entry(release, about, cover, artwork, existing, urls) -> dict:
    """Build the releases.json entry. `existing` (same catalog) keeps manual fields."""
    existing = existing or {}
    tracks = []
    for i, t in enumerate(release.get("tracks", []), 1):
        num = t.get("number", i)
        u128, u320 = urls.get(num, ("", ""))
        tracks.append({
            "number": num,
            "title": t.get("title", ""),
            "runtime": t.get("runtime") or t.get("duration", ""),
            "url": u128,
            "url_320": u320,
        })

    release_date = release.get("release_date", "")
    year = release.get("year") or (release_date[:4] if release_date[:4].isdigit() else "")

    platforms = dict(release.get("platforms") or release.get("plaforms") or {})
    if release.get("bandcamp_url") and not platforms.get("bandcamp"):
        platforms["bandcamp"] = release["bandcamp_url"]

    entry = {
        **existing,
        "catalog": release["catalog"],
        "artist": release.get("artist", ""),
        "title": release.get("title", ""),
        "format": release.get("format") or existing.get("format", ""),
        "year": year or existing.get("year", ""),
        "genre": release.get("genre") or existing.get("genre", ""),
        "about": about,
        "cover": cover or existing.get("cover"),
        "artwork": artwork or existing.get("artwork", {}),
        "platforms": build_platforms(platforms, existing.get("platforms", [])),
        "tracks": tracks,
        "pushed_at": datetime.now(timezone.utc).isoformat(),
    }
    if release_date:
        entry["release_date"] = release_date
    return entry


def write_releases(path: Path, data: dict) -> Path:
    """Validate against the schema, back up the old file, write atomically.
    Raises ValueError (file untouched) if the data violates the schema."""
    import jsonschema

    schema = json.loads((path.parent / "releases.schema.json").read_text())
    errors = sorted(
        jsonschema.Draft7Validator(schema).iter_errors(data),
        key=lambda e: list(e.absolute_path),
    )
    if errors:
        raise ValueError("; ".join(
            f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message[:120]}"
            for e in errors[:5]
        ))

    backups = path.parent / "backups"
    backups.mkdir(exist_ok=True)
    backup = backups / f"releases.{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.json"
    shutil.copy2(path, backup)

    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, path)
    return backup


def push_release(release_path: str):
    path = Path(release_path)

    print(f"\n{Fore.RED}{Style.BRIGHT}THE MOON RECORDS — CDN PUSH{Style.RESET_ALL}")
    print(f"Release: {path.name}\n")

    # ── Load credentials ───────────────────────────────────────────────────────
    header("1. CREDENTIALS")
    env = load_env()
    cdn_base = env.get("CDN_BASE_PATH", "/releases")
    cdn_public = (env.get("CDN_PUBLIC_URL") or "").rstrip("/")
    if not cdn_public:
        fail("CDN_PUBLIC_URL missing in .env — URLs in releases.json would be broken")
        sys.exit(1)
    ok(f"CDN: {env['CDN_HOST']}")

    # ── Load release.json ──────────────────────────────────────────────────────
    header("2. RELEASE DATA")
    json_path = path / "release.json"
    if not json_path.exists():
        fail("release.json not found — run ./tools/tmr generate first")
        sys.exit(1)

    with open(json_path) as f:
        data = json.load(f)

    catalog = data.get("catalog", path.name)
    artist = data.get("artist", "")
    title = data.get("title", "")
    ok(f"{catalog} — {artist} — {title}")

    about_path = path / "about.md"
    about = about_path.read_text(encoding="utf-8").strip() if about_path.exists() else ""
    problems = publish_problems(data, about)
    if problems:
        for pr in problems:
            fail(pr)
        fail("Not publishable yet — nothing was uploaded.")
        sys.exit(1)
    ok("Release data complete (no placeholders)")

    # ── Resolve audio files ────────────────────────────────────────────────────
    header("3. ASSETS")
    slug = path.name

    # Audio — 128k (web player) + 320k (download)
    mp3_128_dir = path / "export" / "mp3" / "128"
    mp3_320_dir = path / "export" / "mp3" / "320"
    # Legacy fallback: export/mp3/ (flat, old convert output)
    mp3_legacy_dir = path / "export" / "mp3"

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
        fail("No MP3s found — run ./tools/tmr convert first")
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
                f"{len(raw_covers)} raw artwork file(s) — run ./tools/tmr convert first for optimised variants"
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
    releases_path = RELEASES_PATH
    repo_root = releases_path.parents[1]

    with open(releases_path) as f:
        releases_data = json.load(f)

    def find_url(url_map: dict, track_num: int) -> str:
        """Match by track number prefix (e.g. '01_')."""
        prefix = str(track_num).zfill(2) + "_"
        for name, url in url_map.items():
            if name.startswith(prefix):
                return url
        return ""

    urls = {
        t.get("number", i): (
            find_url(cdn_audio_map.get("128", {}), t.get("number", i)),
            find_url(cdn_audio_map.get("320", {}), t.get("number", i)),
        )
        for i, t in enumerate(data.get("tracks", []), 1)
    }

    existing = next((r for r in releases_data["releases"] if r["catalog"] == catalog), None)
    if existing:
        info("Existing entry found — keeping its DSP links and manual fields")

    entry = build_entry(
        {**data, "catalog": catalog}, about, cdn_cover, cdn_artwork, existing, urls
    )
    upsert_release(releases_data, entry)
    releases_data["_meta"]["generated"] = datetime.now(timezone.utc).isoformat()

    try:
        backup = write_releases(releases_path, releases_data)
    except ValueError as e:
        fail(f"releases.json NOT written — schema violation: {e}")
        sys.exit(1)

    ok(f"Backup: {backup.relative_to(repo_root)}")
    ok(f"releases.json updated — {len(releases_data['releases'])} release(s)")

    header("8. DONE")
    ok(f"CDN: {cdn_public}/releases/{slug}/")
    info("Next: commit data/releases.json and push the-moon-web")
    print()
