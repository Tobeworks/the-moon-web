"""
server.py — tmr studio HTTP API. Local only: 127.0.0.1, start token, Host check.
"""

import json
import re
import secrets
from datetime import date
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from commands.checks import publish_problems
from studio import dsp, folders, gitops
from studio.config import Config
from studio.jobs import JobBusy, Jobs
from studio.progress import progress
from studio.status import find_folder, list_releases, release_status

CATALOG_RE = re.compile(r"^TMR-\d{3,}$")
RUN_STEPS = {"generate", "validate", "convert", "social"}
CDN_KEYS = ("CDN_HOST", "CDN_USER", "CDN_PUBLIC_URL")
INDEX = Path(__file__).parent / "index.html"
GENRES = ["Ambient", "Dark Ambient", "Drone", "Cinematic", "Electronic"]  # extend here


class NewRelease(BaseModel):
    artist: str
    title: str
    release_date: str = ""
    catalog: str | None = None


class Meta(BaseModel):
    fields: dict = {}
    about: str | None = None


class Paths(BaseModel):
    paths: list[str]
    overwrite: list[str] = []


class Pick(BaseModel):
    kind: str


class Run(BaseModel):
    step: str
    force: bool = False
    format: str | None = None


class Push(BaseModel):
    confirm: str = ""


class Commit(BaseModel):
    message: str = ""


class Links(BaseModel):
    links: list[dict]


def _env_keys(cfg: Config) -> set[str]:
    path = cfg.web_root / ".env"
    if not path.exists():
        return set()
    return {line.split("=", 1)[0].strip() for line in path.read_text().splitlines()
            if "=" in line and not line.startswith("#") and line.split("=", 1)[1].strip()}


def create_app(cfg: Config, token: str, jobs: Jobs | None = None) -> FastAPI:
    app = FastAPI(title="tmr studio", docs_url=None, redoc_url=None, openapi_url=None)
    jobs = jobs or Jobs()
    job_meta: dict[str, dict] = {}

    @app.middleware("http")
    async def guard(request: Request, call_next):
        host = request.headers.get("host", "").rsplit(":", 1)[0]
        if host not in ("127.0.0.1", "localhost"):
            return JSONResponse({"detail": "bad host"}, status_code=400)
        if request.url.path.startswith("/api/"):
            given = request.headers.get("x-studio-token") or request.cookies.get("studio") or ""
            if not secrets.compare_digest(given, token):
                return JSONResponse({"detail": "unauthorized"}, status_code=401)
        return await call_next(request)

    # ── helpers ──────────────────────────────────────────────────────────────
    def entries() -> list[dict]:
        return json.loads(cfg.releases_path.read_text()).get("releases", [])

    def ctx(catalog: str):
        catalog = catalog.upper()
        if not CATALOG_RE.match(catalog):
            raise HTTPException(404, "unknown release")
        entry = next((e for e in entries() if e["catalog"].upper() == catalog), None)
        folder = find_folder(cfg.assets_dir, catalog)
        if entry is None and folder is None:
            raise HTTPException(404, "unknown release")
        return catalog, folder, entry

    def need_folder(folder):
        if folder is None:
            raise HTTPException(400, "no asset folder for this release")
        return folder

    def row(catalog: str) -> dict:
        return next(r for r in list_releases(cfg, date.today()) if r["catalog"].upper() == catalog)

    def release_json(folder: Path | None) -> dict:
        try:
            return json.loads((folder / "release.json").read_text())
        except (OSError, ValueError, TypeError):
            return {}

    def about_of(folder: Path | None) -> str:
        p = folder / "about.md" if folder else None
        return p.read_text(encoding="utf-8") if p and p.exists() else ""

    def mp3_files(folder: Path) -> list[Path]:
        return [f for br in ("128", "320") for f in sorted((folder / "export" / "mp3" / br).glob("*.mp3"))]

    def push_files(folder: Path) -> list[dict]:
        art = sorted(f for ext in ("jpg", "webp") for f in (folder / "export" / "artwork").glob(f"*.{ext}"))
        return ([{"name": f"{f.parent.name}/{f.name}", "size": f.stat().st_size} for f in mp3_files(folder)]
                + [{"name": f.name, "size": f.stat().st_size} for f in art])

    def push_problems(catalog, folder, entry) -> list[str]:
        problems = publish_problems(release_json(folder), about_of(folder))
        st = release_status(entry, folder, None)
        if st["K"] == "stale":
            problems.append("cover changed after conversion — convert again with force")
        elif st["K"] != "ok":
            problems.append("not converted yet")
        return problems

    def start(argv, label, kind=None, total=None):
        try:
            job_id = jobs.start(argv, cfg.web_root, label)
        except JobBusy:
            raise HTTPException(409, "another job is running")
        job_meta[job_id] = {"kind": kind, "total": total}
        return {"job_id": job_id}

    # ── pages ────────────────────────────────────────────────────────────────
    @app.get("/")
    def index(request: Request, key: str | None = None):
        if key is not None:
            if not secrets.compare_digest(key, token):
                raise HTTPException(401, "bad key")
            resp = RedirectResponse("/", status_code=303)
            resp.set_cookie("studio", token, httponly=True, samesite="strict")
            return resp
        if not secrets.compare_digest(request.cookies.get("studio", ""), token):
            raise HTTPException(401, "open the URL printed by `tmr studio`")
        return FileResponse(INDEX)

    # ── state and releases ───────────────────────────────────────────────────
    @app.get("/api/state")
    def state():
        return {"releases": list_releases(cfg, date.today()),
                "next_catalog": folders.next_catalog(entries(), cfg.assets_dir),
                "cdn_configured": all(k in _env_keys(cfg) for k in CDN_KEYS),
                "genres": sorted(set(GENRES) | {e["genre"] for e in entries() if e.get("genre")}),
                "releases_dirty": gitops.releases_dirty(cfg),
                "cdn_missing": [k for k in CDN_KEYS if k not in _env_keys(cfg)],
                "job": jobs.current()}

    @app.post("/api/releases", status_code=201)
    def create(body: NewRelease):
        catalog = (body.catalog or folders.next_catalog(entries(), cfg.assets_dir)).upper()
        if not CATALOG_RE.match(catalog):
            raise HTTPException(400, "catalog must look like TMR-018")
        if not body.artist.strip() or not body.title.strip():
            raise HTTPException(400, "artist and title are required")
        if any(e["catalog"].upper() == catalog for e in entries()):
            raise HTTPException(409, "catalog exists")
        try:
            d = folders.create_release(cfg.assets_dir, catalog, body.artist.strip(),
                                       body.title.strip(), body.release_date)
        except FileExistsError:
            raise HTTPException(409, "catalog exists")
        return {"catalog": catalog, "folder": d.name}

    @app.get("/api/releases/{catalog}")
    def detail(catalog: str):
        catalog, folder, entry = ctx(catalog)
        names = lambda sub, exts: sorted(  # noqa: E731
            f.name for f in (folder / sub).glob("*") if f.suffix.lower() in exts) if folder else []
        return {"summary": row(catalog), "release": release_json(folder), "entry": entry,
                "about": about_of(folder),
                "files": {"audio": names("audio", folders.AUDIO_EXT),
                          "artwork": names("artwork", folders.IMAGE_EXT),
                          "mp3": [f"{f.parent.name}/{f.name}" for f in mp3_files(folder)] if folder else []}}

    @app.put("/api/releases/{catalog}/meta")
    def meta(catalog: str, body: Meta):
        _, folder, _ = ctx(catalog)
        try:
            release = folders.write_meta(need_folder(folder), body.fields, body.about)
        except ValueError as e:
            raise HTTPException(400, str(e))
        return {"release": release}

    # ── files ────────────────────────────────────────────────────────────────
    @app.post("/api/releases/{catalog}/files")
    def add_files(catalog: str, body: Paths):
        _, folder, _ = ctx(catalog)
        paths = [Path(p) for p in body.paths]
        if any(not p.is_absolute() or not p.exists() for p in paths):
            raise HTTPException(400, "paths must be existing absolute paths")
        return folders.copy_files(need_folder(folder), paths, frozenset(body.overwrite))

    @app.post("/api/releases/{catalog}/upload")
    async def upload(catalog: str, files: list[UploadFile] = File(...), overwrite: bool = Form(False)):
        _, folder, _ = ctx(catalog)
        folder = need_folder(folder)
        plan = []
        for f in files:
            name = Path(f.filename or "").name
            kind = folders.classify(Path(name))
            if kind and not name.startswith("."):
                plan.append((f, folder / kind / name))
        conflicts = [t.name for _, t in plan if t.exists()]
        if conflicts and not overwrite:
            raise HTTPException(409, {"conflicts": conflicts})
        for f, target in plan:
            with open(target, "wb") as out:
                while chunk := await f.read(1024 * 1024):
                    out.write(chunk)
        return {"copied": [t.name for _, t in plan],
                "skipped": [Path(f.filename or "").name for f in files
                            if Path(f.filename or "").name not in {t.name for _, t in plan}]}

    @app.post("/api/pick")
    def pick(body: Pick):
        if body.kind not in ("files", "folder", "cover"):
            raise HTTPException(400, "kind must be files, folder or cover")
        return {"paths": [str(p) for p in folders.pick_paths(body.kind)]}

    # ── jobs ─────────────────────────────────────────────────────────────────
    @app.post("/api/releases/{catalog}/run")
    def run(catalog: str, body: Run):
        catalog, folder, _ = ctx(catalog)
        if body.step not in RUN_STEPS:
            raise HTTPException(400, f"step must be one of {sorted(RUN_STEPS)}")
        argv = [str(cfg.tmr), body.step, str(need_folder(folder))]
        if body.step == "convert" and body.force:
            argv.append("--force")
        if body.step == "social" and body.format in ("square", "reel", "all"):
            argv += ["--format", body.format]
        total = len(release_json(folder).get("tracks") or []) * 2 if body.step == "convert" else None
        return start(argv, f"{body.step} {catalog}", body.step, total)

    @app.get("/api/releases/{catalog}/push-preview")
    def push_preview(catalog: str):
        catalog, folder, entry = ctx(catalog)
        files = push_files(need_folder(folder))
        public = (cfg.web_root / ".env").read_text() if (cfg.web_root / ".env").exists() else ""
        base = next((l.split("=", 1)[1].strip() for l in public.splitlines()
                     if l.startswith("CDN_PUBLIC_URL=")), "")
        return {"files": files, "total_bytes": sum(f["size"] for f in files),
                "target": f"{base}/releases/{folder.name}/",
                "problems": push_problems(catalog, folder, entry)}

    @app.post("/api/releases/{catalog}/push")
    def push(catalog: str, body: Push):
        catalog, folder, entry = ctx(catalog)
        if body.confirm.strip().upper() != catalog:
            raise HTTPException(400, f"type {catalog} to confirm the upload")
        problems = push_problems(catalog, need_folder(folder), entry)
        if problems:
            raise HTTPException(400, "; ".join(problems))
        missing = [k for k in CDN_KEYS if k not in _env_keys(cfg)]
        if missing:
            raise HTTPException(400, f"missing in .env: {', '.join(missing)}")
        return start([str(cfg.tmr), "push", str(folder)], f"push {catalog}", "push",
                     len(push_files(folder)))

    @app.get("/api/jobs/{job_id}")
    def job(job_id: str, since: int = 0):
        j = jobs.get(job_id, since)
        if j is None:
            raise HTTPException(404, "unknown job")
        meta = job_meta.get(job_id, {})
        full = jobs.get(job_id, 0)["lines"] if meta.get("total") else []
        return {**j, "kind": meta.get("kind"), "progress": progress(meta.get("kind"), full, meta.get("total"))}

    @app.post("/api/jobs/{job_id}/cancel")
    def job_cancel(job_id: str):
        return {"cancelled": jobs.cancel(job_id)}

    @app.post("/api/git/commit")
    def git_commit(body: Commit):
        try:
            return {"commit": gitops.commit_releases(cfg, body.message)}
        except ValueError as e:
            raise HTTPException(400, str(e))
        except RuntimeError as e:
            raise HTTPException(502, str(e))

    # ── dsp ──────────────────────────────────────────────────────────────────
    @app.post("/api/releases/{catalog}/dsp/scan")
    def dsp_scan(catalog: str):
        catalog, folder, entry = ctx(catalog)
        source = entry or release_json(folder)
        plats = source.get("platforms") or []
        if isinstance(plats, dict):
            plats = [{"name": k, "url": v} for k, v in plats.items() if v]
        url = next((p["url"] for p in plats if p.get("name") == "bandcamp" and p.get("url")), "")
        if not url:
            raise HTTPException(400, "add the Bandcamp URL first")
        try:
            result = dsp.scan(cfg, url)
        except (RuntimeError, ValueError, OSError) as e:
            raise HTTPException(502, str(e))
        return {"candidates": dsp.candidates(result, source.get("artist", ""), plats),
                "errors": dsp.scan_errors(result)}

    @app.post("/api/releases/{catalog}/dsp/apply")
    def dsp_apply(catalog: str, body: Links):
        catalog, _, entry = ctx(catalog)
        if entry is None:
            raise HTTPException(400, "push the release first")
        try:
            backup = dsp.apply_links(cfg.releases_path, catalog, body.links)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except KeyError:
            raise HTTPException(404, "unknown release")
        return {"backup": backup.name}

    return app
