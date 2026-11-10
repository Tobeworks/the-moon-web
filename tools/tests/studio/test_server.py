import json
import os
import shutil

import pytest
from fastapi.testclient import TestClient

from studio import dsp
from studio.jobs import JobBusy
from studio.server import create_app

TOKEN = "t"
BASE = "http://127.0.0.1:8765"


class FakeJobs:
    def __init__(self):
        self.started, self.busy = [], False

    def start(self, argv, cwd, label):
        if self.busy:
            raise JobBusy("x")
        self.started.append(argv)
        return "job1"

    def get(self, job_id, since=0):
        return {"id": job_id, "label": "x", "status": "ok", "exit_code": 0, "lines": ["hi"], "next": 1} \
            if job_id == "job1" else None

    def current(self):
        return None


@pytest.fixture
def jobs():
    return FakeJobs()


@pytest.fixture
def client(studio_env, jobs):
    return TestClient(create_app(studio_env, TOKEN, jobs), base_url=BASE,
                      headers={"X-Studio-Token": TOKEN})


@pytest.fixture
def folder(studio_env, release_dir):
    """A ready release TMR-099 in the temp assets dir (valid, converted)."""
    dest = studio_env.assets_dir / release_dir.name
    shutil.copytree(release_dir, dest)
    for br in ("128", "320"):
        d = dest / "export" / "mp3" / br
        d.mkdir(parents=True)
        (d / "01_first.mp3").write_bytes(b"x" * 10)
        os.utime(d / "01_first.mp3", (4_000_000_000, 4_000_000_000))
    art = dest / "export" / "artwork"
    art.mkdir()
    (art / "cover_600.jpg").write_bytes(b"y" * 5)
    return dest


def test_no_token_is_401(studio_env):
    c = TestClient(create_app(studio_env, TOKEN, FakeJobs()), base_url=BASE)
    assert c.get("/api/state").status_code == 401


def test_foreign_host_is_400(studio_env):
    c = TestClient(create_app(studio_env, TOKEN, FakeJobs()), base_url="http://evil.example",
                   headers={"X-Studio-Token": TOKEN})
    assert c.get("/api/state").status_code == 400


@pytest.mark.parametrize("path", ["/api/releases/..%2Fx", "/api/releases/tmr-1",
                                  "/api/releases/TMR-500", "/api/releases/x"])
def test_bad_catalog_is_404(client, path):
    assert client.get(path).status_code == 404


def test_create_then_state_lists_release(client, studio_env):
    nums = [int(r["catalog"][4:]) for r in json.loads(studio_env.releases_path.read_text())["releases"]]
    new, after = f"TMR-{max(nums) + 1:03d}", f"TMR-{max(nums) + 2:03d}"
    r = client.post("/api/releases", json={"artist": "Logic Moon", "title": "New One",
                                           "release_date": "2026-12-24"})
    assert r.status_code == 201 and r.json()["catalog"] == new
    state = client.get("/api/state").json()
    assert new in [x["catalog"] for x in state["releases"]]
    assert state["next_catalog"] == after
    assert client.post("/api/releases", json={"artist": "a", "title": "b", "catalog": new}
                       ).status_code == 409


def test_meta_unknown_field_is_400(client, folder):
    assert client.put("/api/releases/TMR-099/meta", json={"fields": {"tracks": []}}).status_code == 400
    r = client.put("/api/releases/TMR-099/meta", json={"fields": {"artist": "New"}, "about": "# x\n\ny"})
    assert r.status_code == 200 and r.json()["release"]["artist"] == "New"


def test_files_copy_and_conflict(client, folder, tmp_path):
    src = tmp_path / "in.wav"
    src.write_bytes(b"w")
    body = {"paths": [str(src)]}
    assert client.post("/api/releases/TMR-099/files", json=body).json()["copied"] == ["in.wav"]
    assert client.post("/api/releases/TMR-099/files", json=body).json()["conflicts"] == ["in.wav"]
    assert client.post("/api/releases/TMR-099/files", json={"paths": ["rel/path.wav"]}).status_code == 400


def test_upload_streams_and_conflicts(client, folder):
    files = [("files", ("up.wav", b"abc", "audio/wav"))]
    assert client.post("/api/releases/TMR-099/upload", files=files).status_code == 200
    assert (folder / "audio" / "up.wav").read_bytes() == b"abc"
    r = client.post("/api/releases/TMR-099/upload", files=[("files", ("up.wav", b"zzz", "audio/wav"))])
    assert r.status_code == 409 and (folder / "audio" / "up.wav").read_bytes() == b"abc"


def test_run_builds_tmr_argv(client, folder, jobs, studio_env):
    r = client.post("/api/releases/TMR-099/run", json={"step": "convert", "force": True})
    assert r.status_code == 200 and r.json()["job_id"] == "job1"
    assert jobs.started[-1] == [str(studio_env.tmr), "convert", str(folder), "--force"]
    assert client.post("/api/releases/TMR-099/run", json={"step": "rm -rf"}).status_code == 400


def test_second_job_is_409(client, folder, jobs):
    jobs.busy = True
    assert client.post("/api/releases/TMR-099/run", json={"step": "validate"}).status_code == 409


def test_push_requires_confirm(client, folder, jobs):
    assert client.post("/api/releases/TMR-099/push", json={}).status_code == 400
    assert client.post("/api/releases/TMR-099/push", json={"confirm": "TMR-001"}).status_code == 400
    assert jobs.started == []


def test_push_refused_with_placeholders(client, folder, jobs):
    p = folder / "release.json"
    d = json.loads(p.read_text())
    d["artist"] = "FILL_IN"
    p.write_text(json.dumps(d))
    r = client.post("/api/releases/TMR-099/push", json={"confirm": "TMR-099"})
    assert r.status_code == 400 and jobs.started == []


def test_push_starts_job_when_ready(client, folder, jobs, studio_env):
    r = client.post("/api/releases/TMR-099/push", json={"confirm": "tmr-099"})
    assert r.status_code == 200
    assert jobs.started == [[str(studio_env.tmr), "push", str(folder)]]


def test_push_refused_without_cdn_config(client, folder, jobs, studio_env):
    (studio_env.web_root / ".env").write_text("")
    assert client.post("/api/releases/TMR-099/push", json={"confirm": "TMR-099"}).status_code == 400


def test_push_preview_lists_mp3_and_artwork(client, folder):
    p = client.get("/api/releases/TMR-099/push-preview").json()
    names = {f["name"] for f in p["files"]}
    assert {"128/01_first.mp3", "320/01_first.mp3", "cover_600.jpg"} <= names
    assert p["total_bytes"] == 25 and p["problems"] == []


def test_cdn_configured_flag_does_not_leak_values(client):
    r = client.get("/api/state")
    assert r.json()["cdn_configured"] is True
    assert "secret-pw" not in r.text


SCAN = {"results": {"deezer": {"url": "https://deezer.com/album/1", "matched_artist": "Logic Moon",
                               "confidence": 99}}}


def test_dsp_scan_requires_bandcamp(client, folder):
    p = folder / "release.json"
    d = json.loads(p.read_text())
    d["platforms"] = {}
    p.write_text(json.dumps(d))
    assert client.post("/api/releases/TMR-099/dsp/scan").status_code == 400


def test_dsp_scan_and_apply(client, studio_env, monkeypatch):
    monkeypatch.setattr(dsp, "scan", lambda cfg, url: SCAN)
    data = json.loads(studio_env.releases_path.read_text())
    entry = next(r for r in data["releases"]
                 if not any(p["name"] == "deezer" for p in r["platforms"])
                 and any(p["name"] == "bandcamp" for p in r["platforms"]))
    cat = entry["catalog"]
    entry["artist"] = "Logic Moon"
    studio_env.releases_path.write_text(json.dumps(data))
    found = client.post(f"/api/releases/{cat}/dsp/scan").json()["candidates"]
    assert found[0]["name"] == "deezer" and found[0]["accepted"]
    r = client.post(f"/api/releases/{cat}/dsp/apply", json={"links": [found[0]]})
    assert r.status_code == 200
    saved = next(x for x in json.loads(studio_env.releases_path.read_text())["releases"]
                 if x["catalog"] == cat)
    assert saved["platforms"][-1]["name"] == "deezer"
    assert client.post(f"/api/releases/{cat}/dsp/apply",
                       json={"links": [{"name": "deezer", "url": ""}]}).status_code == 400


def test_index_served_with_key(studio_env):
    c = TestClient(create_app(studio_env, TOKEN, FakeJobs()), base_url=BASE)
    assert c.get("/").status_code == 401
    assert c.get("/?key=wrong").status_code == 401
    r = c.get(f"/?key={TOKEN}", follow_redirects=False)
    assert r.status_code == 303 and "studio=" in r.headers["set-cookie"]
    page = c.get("/")
    assert page.status_code == 200 and "tmr studio" in page.text
