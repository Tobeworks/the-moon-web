# tmr studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A local browser UI (`./tools/tmr studio`) that creates releases, copies files, edits metadata, runs convert/push, and adds DSP links, on top of the existing `tmr` CLI.

**Architecture:** FastAPI server in `tools/studio/` (127.0.0.1 only, per-start token). Pure functions compute release status from `data/releases.json`, the asset folders and `git`. Long tasks run `./tools/tmr …` as one subprocess at a time; the page polls the log. One `index.html`, no build step.

**Tech Stack:** Python 3.13+, FastAPI, uvicorn, python-multipart, pytest + httpx (`TestClient`), vanilla JS.

**Spec:** `docs/superpowers/specs/2026-11-10-tmr-studio-design.md`

## Global Constraints

- Only macOS; server binds `127.0.0.1`; every request needs the start token (cookie or `X-Studio-Token`) and a `Host` of `127.0.0.1:<port>` or `localhost:<port>`.
- No second database. Status is computed from files each time.
- No build step for the frontend; no CDN scripts. Google Fonts link only (Josefin Sans, Space Mono), fallbacks `Futura, Arial` and `Courier New`.
- UI sizes: body text ≥ 18 px, rows and inputs ≥ 48 px, smallest label 14 px, click targets ≥ 44 px, ≥ 24 px between panels. Colors from `src/styles/global.css` (`#0C0C0C`, `#E8E4D8`, accent `#C4B98A`). Status never by color alone.
- Push to the CDN only via `POST …/push` with `confirm` equal to the catalog; nothing else may start a push.
- Tests use temp dirs, never the CDN, never the repo's `data/releases.json`.
- Platform names only from `commands.checks.PLATFORM_NAMES`; never write empty URLs.
- Commits: Conventional Commits, one short English line, trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. No push.

## Review Focus

- Old release in `releases.json` without asset folder → A/V/K are `na`, not open (`test_old_release_without_folder_is_na`).
- Mixed date formats (`2025-06-03T00:00:00+00:00` and `2026-11-13`) → `days_until` works for both (`test_days_until_both_formats`).
- Catalog in a URL path like `../x` or `tmr-1` is rejected before touching the filesystem (`test_bad_catalog_is_404`).
- Copying a file whose name exists is reported as conflict and not overwritten (`test_copy_conflict_not_overwritten`).
- A second job while one runs → 409; push without matching `confirm` → 400 (`test_second_job_is_409`, `test_push_requires_confirm`).

---

## File Structure

| File | Responsibility |
|---|---|
| `tools/studio/config.py` | `Config`, `load_config()` |
| `tools/studio/status.py` | step status, next step, dates, release list, git comparison |
| `tools/studio/folders.py` | catalog numbers, folder creation, file copy, meta writing, macOS pick dialog |
| `tools/studio/jobs.py` | one-at-a-time subprocess runner with log |
| `tools/studio/dsp.py` | scraper run, candidate filtering, applying links |
| `tools/studio/server.py` | `create_app(cfg, token, jobs=None)` and all routes |
| `tools/studio/index.html` | the whole UI |
| `tools/the-moon.py` | new command `studio` |
| `tools/tests/studio/…` | tests, one file per module |

Shared fixtures go in `tools/tests/conftest.py` (extend `release_dir`); add `studio_env` fixture there: a temp web root with `data/releases.json` (+ schema copy) and temp assets dir.

---

### Task 1: Config and status

**Files:** Create `tools/studio/__init__.py`, `config.py`, `status.py`; Modify `tools/requirements.txt` (`fastapi>=0.110`, `uvicorn>=0.29`, `python-multipart>=0.0.9`), `requirements-dev.txt` (`httpx>=0.27`); Test `tools/tests/studio/test_status.py`

**Interfaces:**
- Produces:
  - `Config(web_root: Path, assets_dir: Path, scraper_dir: Path)` frozen dataclass with properties `releases_path`, `tmr`; `load_config() -> Config` (env `TMR_ASSETS_DIR`, `TMR_SCRAPER_DIR` override; defaults `<web_root>/../the-moon-assets`, `/Users/tobe/Sites/logic-moon.de/dsp_scraper`).
  - `STEPS = ("A","V","K","P","G","D")`
  - `find_folder(assets_dir: Path, catalog: str) -> Path | None` (dir whose name starts with `catalog.lower() + "-"`)
  - `release_status(entry: dict | None, folder: Path | None, committed: dict | None) -> dict[str, str]`, values `ok|open|stale|na|warn`
  - `next_step(status: dict) -> str | None`
  - `days_until(release_date: str | None, today: date) -> int | None`
  - `committed_entries(cfg: Config) -> dict[str, dict]` (catalog → entry from `git show HEAD:data/releases.json`, `{}` on error)
  - `list_releases(cfg: Config, today: date) -> list[dict]` with keys `catalog, artist, title, release_date, days_until, upcoming, status, next`; sorted by date descending, undated first; includes asset folders with no entry yet.

Rules: **A** ok = folder has ≥1 audio file in `audio/` and an image in `artwork/`. **V** ok = `commands.checks.publish_problems(release_json, about) == []` and every track `file` exists. **K** ok = for each track number an `NN_*.mp3` exists in `export/mp3/128` and `320`; `stale` if `commands.convert.cover_is_newer`. **P** ok = entry has `pushed_at`. **G** = `open` if no entry, `warn` if entry != committed entry (or not committed), else `ok`. **D** ok = entry platforms with non-empty URL include `spotify, apple_music, amazon_music, deezer`. Without folder: A/V/K are `na` if the entry exists, else `open`. `next_step` = first step in `STEPS` that is not `ok` or `na`.

- [ ] **Step 1: Write failing tests** in `test_status.py` (use `release_dir`/`tmp_path`):
  - `test_a_ok_needs_audio_and_cover`: empty `audio/` → `open`; fixture folder → `ok`.
  - `test_v_open_with_fill_in`: set `artist: "FILL_IN"` → `status["V"] == "open"`.
  - `test_k_stale_when_cover_newer`: create `export/mp3/128/01_x.mp3` and `320/01_x.mp3`, `os.utime` cover newer → `"stale"`; older → `"ok"`.
  - `test_old_release_without_folder_is_na`: entry with `pushed_at`, `folder=None` → A,V,K `"na"`, P `"ok"`.
  - `test_g_warn_when_not_committed`: `committed=None` → `"warn"`; equal entry → `"ok"`.
  - `test_d_needs_four_dsps`: three links → `open`, four → `ok`; entry with `{"name":"spotify","url":""}` doesn't count.
  - `test_next_step_skips_na`: `{"A":"na","V":"na","K":"na","P":"ok","G":"warn","D":"open"}` → `"G"`; all ok → `None`.
  - `test_days_until_both_formats`: `"2026-11-13"` and `"2026-11-13T00:00:00+00:00"` with today `2026-11-10` → `3`; past date → negative; `None` → `None`.
  - `test_list_releases_includes_folder_without_entry_and_sorts`: folder `tmr-099-…` not in releases → listed first with `next == "V"` or earliest open step.
- [ ] **Step 2:** `cd tools && source venv/bin/activate && pip install -q -r requirements-dev.txt && python -m pytest tests/studio/test_status.py -q` → FAIL (import error).
- [ ] **Step 3:** Implement `config.py` and `status.py` as specified.
- [ ] **Step 4:** Same pytest command → PASS.
- [ ] **Step 5:** `git add tools && git commit -m "feat(studio): config and status"` (with trailer).

---

### Task 2: Folders and files

**Files:** Create `tools/studio/folders.py`; Test `tools/tests/studio/test_folders.py`

**Interfaces:**
- Consumes: `commands.checks.PLATFORM_NAMES`.
- Produces:
  - `slug(text: str) -> str` (ASCII lowercase, non-alphanumerics → `-`, trimmed)
  - `next_catalog(entries: list[dict], assets_dir: Path) -> str` (`"TMR-018"`: highest number among entries and folders + 1, 3 digits)
  - `create_release(assets_dir: Path, catalog: str, artist: str, title: str, release_date: str = "") -> Path` creates `tmr-NNN-<artist>-<title>/{audio,artwork}` and a minimal `release.json` (`catalog, release_id, artist, title, release_date, label, format "EP"`); raises `FileExistsError` if a folder for the catalog exists.
  - `classify(path: Path) -> str | None` → `"audio"` (`.wav .aif .aiff`) / `"artwork"` (`.png .jpg .jpeg .tif .tiff`) / `None`
  - `copy_files(release_dir: Path, sources: list[Path], overwrite: frozenset[str] = frozenset()) -> dict` → `{"copied": [...], "conflicts": [...], "skipped": [...]}`; a directory source contributes its files (one level); never overwrites unless the name is in `overwrite`; unsupported types go to `skipped`.
  - `write_meta(release_dir: Path, fields: dict, about: str | None) -> dict` updates only `artist, title, release_date, format, genre, year` and `bandcamp` (→ `platforms.bandcamp`); raises `ValueError` if `release.json` is missing or a field is unknown; writes `about.md` when `about` is not `None`; returns the new release dict.
  - `pick_paths(kind: str) -> list[Path]` (`"files" | "folder" | "cover"`) via `osascript` `choose file`/`choose folder`; returns `[]` when cancelled.

- [ ] **Step 1: Failing tests:**
  - `test_next_catalog`: entries up to `TMR-017`, folder `tmr-018-…` → `"TMR-019"`; nothing → `"TMR-001"`.
  - `test_create_release_makes_structure`: folder name `tmr-018-logic-moon-stellar-refuge`, `audio/`, `artwork/` exist, `release.json["catalog"] == "TMR-018"`; second call raises `FileExistsError`.
  - `test_slug_strips_accents_and_symbols`: `slug("Réunion & Co.") == "reunion-co"`.
  - `test_copy_sorts_audio_and_cover`: `.wav` → `audio/`, `.png` → `artwork/`, `.txt` in `skipped`.
  - `test_copy_conflict_not_overwritten`: same name twice → second call has it in `conflicts`, file content unchanged; with `overwrite={name}` → replaced.
  - `test_copy_folder_source`: directory with two wavs → both copied.
  - `test_write_meta_updates_and_rejects_unknown`: `artist` changed in file; `{"tracks": []}` raises `ValueError`; `about` written to `about.md`; `bandcamp` lands in `platforms.bandcamp`.
- [ ] **Step 2:** run `pytest tests/studio/test_folders.py -q` → FAIL.
- [ ] **Step 3:** Implement `folders.py` (osascript: `subprocess.run(["osascript","-e",script])`, parse POSIX paths; cancel returns non-zero → `[]`).
- [ ] **Step 4:** PASS. **Step 5:** commit `feat(studio): folders and file copy`.

---

### Task 3: Job runner

**Files:** Create `tools/studio/jobs.py`; Test `tools/tests/studio/test_jobs.py`

**Interfaces:**
- Produces: `class JobBusy(Exception)`; `class Jobs` with `start(argv: list[str], cwd: Path, label: str) -> str` (raises `JobBusy` while one runs), `get(job_id: str, since: int = 0) -> dict | None` → `{"id","label","status": "running"|"ok"|"failed","exit_code","lines": [...since...],"next": int}`, `current() -> dict | None`. Runs `subprocess.Popen(argv, cwd, stdout=PIPE, stderr=STDOUT, text=True, env={**os.environ,"PYTHONUNBUFFERED":"1"})` in a thread; strips ANSI escapes; keeps the last 5000 lines.

- [ ] **Step 1: Failing tests** (argv `[sys.executable, "-c", …]`): `test_job_collects_lines_and_exit_ok` (prints 2 lines → status `ok`, lines match, `next == 2`); `test_failed_exit_code` (`sys.exit(3)` → `failed`, `exit_code == 3`); `test_ansi_is_stripped` (`\x1b[32m✓\x1b[0m` → `✓`); `test_second_job_is_busy` (sleep job running → `JobBusy`); `test_since_returns_only_new_lines`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS (helper waits with timeout 5 s). **Step 5:** commit `feat(studio): job runner`.

---

### Task 4: DSP helpers

**Files:** Create `tools/studio/dsp.py`; Test `tools/tests/studio/test_dsp.py`

**Interfaces:**
- Consumes: `commands.push.write_releases`, `commands.checks.PLATFORM_NAMES`.
- Produces:
  - `candidates(scraper_json: dict, artist: str, existing: list[dict]) -> list[dict]` → items `{"name","url","confidence","matched_artist","accepted": bool,"reason": str}`; only platforms in `PLATFORM_NAMES`, only with a URL, skipping names already present with a non-empty URL. `accepted` = confidence ≥ 85 **and** non-empty `matched_artist` containing/contained in `artist` (case-insensitive); otherwise `reason` says why ("confidence 71 < 85", "artist differs", "no matched_artist").
  - `scan(cfg: Config, bandcamp_url: str) -> dict`: `subprocess.run(["uv","run","python","cli.py",url,"--stdout"], cwd=cfg.scraper_dir, capture_output, timeout=240)`; returns parsed JSON; raises `RuntimeError(stderr)` on non-zero.
  - `apply_links(releases_path: Path, catalog: str, links: list[dict]) -> Path`: appends `{"name","url"}` for valid names with non-empty URL not yet present (existing entries untouched), then `write_releases`; raises `KeyError` for unknown catalog, `ValueError` for invalid name or empty URL; returns backup path.

- [ ] **Step 1: Failing tests** with a sample result copied from the scraper format (`results.spotify.url/matched_artist/confidence`): `test_accepts_only_high_confidence_with_artist` (100/“Logic Moon” accepted; 71 not; url null skipped; `youtube_music` ignored); `test_artist_mismatch_not_accepted` (“Other Band”); `test_existing_platform_is_skipped`; `test_apply_appends_and_keeps_order` (copy of real `data/releases.json` in tmp, schema alongside; existing links untouched, new one last, backup exists); `test_apply_rejects_empty_url_and_unknown_name`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS. **Step 5:** commit `feat(studio): dsp candidates and apply`.

---

### Task 5: Server API

**Files:** Create `tools/studio/server.py`; Test `tools/tests/studio/test_server.py`; extend `tools/tests/conftest.py` with `studio_env` (temp `Config`, `data/releases.json` + schema copied from the repo, assets dir).

**Interfaces:**
- Consumes: everything from Tasks 1–4.
- Produces: `create_app(cfg: Config, token: str, jobs: Jobs | None = None) -> FastAPI`.

Routes (all `/api/*` need cookie `studio=<token>` or header `X-Studio-Token`; any request with a `Host` other than `127.0.0.1:*`/`localhost:*` → 400):

| Route | Behavior |
|---|---|
| `GET /` | needs `?key=<token>` once → sets cookie, redirects to `/`; serves `index.html` |
| `GET /api/state` | `{"releases": list_releases(...), "next_catalog", "cdn_configured": bool, "job": current}`; `cdn_configured` = `CDN_HOST`, `CDN_USER`, `CDN_PUBLIC_URL` present in `<web_root>/.env` (values never returned) |
| `POST /api/releases` | `{artist,title,release_date,catalog?}` → `create_release`; 201 `{catalog}`; 409 if exists |
| `GET /api/releases/{catalog}` | summary + `release` (release.json) + `about` + file lists (`audio`, `artwork`, `mp3`) |
| `PUT /api/releases/{catalog}/meta` | `{fields, about?}` → `write_meta`; 400 on `ValueError` |
| `POST /api/releases/{catalog}/files` | `{paths:[...], overwrite:[...]}` → `copy_files`; paths must be existing absolute paths |
| `POST /api/releases/{catalog}/upload` | multipart `files`; streamed to disk in chunks into the right subfolder, never overwriting (409 listing conflicts) |
| `POST /api/pick` | `{kind}` → `{paths}` via `pick_paths` |
| `POST /api/releases/{catalog}/run` | `{step: "generate"|"validate"|"convert"|"social", force?, format?}` → job via `./tools/tmr <step> <folder> [--force|--format X]`; 409 when busy |
| `GET /api/releases/{catalog}/push-preview` | `{files: [{name,size}], total_bytes, target, problems: [...]}` (problems = `publish_problems` + V/K not ok) |
| `POST /api/releases/{catalog}/push` | `{confirm}` must equal catalog (400 otherwise); refuses (400) with problems; starts `./tools/tmr push <folder>` job; 409 when busy |
| `GET /api/jobs/{id}?since=N` | `Jobs.get` or 404 |
| `POST /api/releases/{catalog}/dsp/scan` | needs `platforms.bandcamp` (400 otherwise); returns `candidates(...)`; 502 on scraper failure |
| `POST /api/releases/{catalog}/dsp/apply` | `{links}` → `apply_links`; 400/404 mapped from exceptions |

`{catalog}` must match `^TMR-\d{3,}$` (case-insensitive, uppercased) and have a folder or an entry, else 404.

- [ ] **Step 1: Failing tests** (`TestClient(app, base_url="http://127.0.0.1:8765", headers={"X-Studio-Token": "t"})`, fake `Jobs` that records argv): `test_no_token_is_401`; `test_foreign_host_is_400`; `test_bad_catalog_is_404` (`/api/releases/..%2Fx`, `/api/releases/tmr-1`); `test_create_then_state_lists_release`; `test_meta_unknown_field_is_400`; `test_files_copy_and_conflict`; `test_upload_streams_and_conflicts`; `test_run_builds_tmr_argv` (`["…/tools/tmr","convert",<folder>,"--force"]`); `test_second_job_is_409`; `test_push_requires_confirm` (wrong/missing → 400, no job started); `test_push_refused_with_placeholders` (400, no job); `test_push_starts_job_when_ready` (V and K ok in tmp folder, correct confirm → argv `[…,"push",<folder>]`); `test_push_preview_lists_mp3_and_artwork`; `test_dsp_scan_requires_bandcamp`; `test_dsp_apply_writes_link` (monkeypatch `dsp.scan` to sample JSON); `test_cdn_configured_flag_does_not_leak_values`.
- [ ] **Step 2:** FAIL. **Step 3:** implement `server.py` (helpers `_folder(catalog)`, auth/host middleware, `HTTPException`s). **Step 4:** PASS. **Step 5:** commit `feat(studio): server api`.

---

### Task 6: UI page

**Files:** Create `tools/studio/index.html`; Test: one case in `test_server.py` (`test_index_served_with_key`: `GET /?key=t` sets cookie and then `/` returns HTML containing `tmr studio`).

Contents (spec sections 6 and 8; mockup `…/ui-layout-v2.html` is the structure reference): header with git/CDN status and nav; **Übersicht** (stats, table, six step boxes with letter + tooltip, next-step button, legend); **Release** (step rail + panels Assets / Metadaten / Konvertieren / Push / DSP-Links, log pane polling `/api/jobs/{id}?since=` every 500 ms); **Neu anlegen**. Asset panel: drag & drop (uploads) plus buttons "Dateien wählen …", "Ordner wählen …", "Cover wählen …" (call `/api/pick`, then `/files`); conflicts ask before overwriting. Push button opens a confirm dialog with the preview and requires typing the catalog. Missing CDN config shows a banner naming the missing `.env` keys. Sizes and colors exactly as in Global Constraints. No visual self-verification (user checks in the browser).

- [ ] **Step 1:** add the failing test. **Step 2:** FAIL (no file). **Step 3:** write `index.html`. **Step 4:** PASS. **Step 5:** commit `feat(studio): ui page`.

---

### Task 7: CLI command and docs

**Files:** Modify `tools/the-moon.py`, `tools/README.md`, `AGENTS.md` (web repo); Test `tools/tests/studio/test_cli.py`

**Interfaces:** `studio` click command: options `--port` (default 8765), `--no-open`; generates `secrets.token_urlsafe(16)`, prints `http://127.0.0.1:<port>/?key=<token>`, opens it with `webbrowser` unless `--no-open`, runs `uvicorn.run(create_app(load_config(), token), host="127.0.0.1", port=port)`.

- [ ] **Step 1: Failing test:** `CliRunner().invoke(cli, ["studio","--help"])` exit 0 and output mentions `--port`.
- [ ] **Step 2:** FAIL. **Step 3:** implement the command; in `tools/README.md` add a "Studio" section (start command, what it does, `.env` CDN keys, tests command); in the web `AGENTS.md` add a short "Toolchain" section (`./tools/tmr …`, studio, data flow `tmr push → data/releases.json → commit → push`, pitfalls from the old OS AGENTS: empty platform URLs, future release date, platform names tied to `src/assets/dsp/`, scraper matches need artist check). Keep the existing agent rules unchanged.
- [ ] **Step 4:** full run `cd tools && python -m pytest tests -q` → all pass. Smoke: `./tools/tmr studio --no-open --port 8799` starts, `curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8799/?key=<token from output>"` prints `200` (or the redirect `303` then `200`), then stop it.
- [ ] **Step 5:** commit `feat(studio): studio command and docs`.

---

## Self-review

- **Spec coverage:** overview/status (T1), folders and file dialogs/drop (T2, T5, T6), jobs and log (T3), DSP rules (T4), token/host protection and push gate (T5), UI sizes (T6), start command (T7), tests (all). Phase 2 items (DSP scraper, social) are included as T4/T5 routes. `.app` launcher, Windows/Linux and Playwright stay out as in the spec.
- **Deliberate deviations from the spec:** log delivered by polling (`/api/jobs/{id}?since=N`) instead of Server-Sent Events (same result, simpler to test); V uses `publish_problems` plus file checks instead of running `validate` (resolution is still checked at push-time by the CLI and at `validate`); G compares each entry with `git show HEAD:data/releases.json` instead of one global flag.
- **Type consistency:** `Config`, `Jobs`, `list_releases`, `release_status`, `candidates`, `apply_links`, `write_releases` signatures are used identically in T5.
