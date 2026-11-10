"""
jobs.py — runs one subprocess at a time and keeps its output for polling.
"""

import os
import re
import subprocess
import threading
import uuid
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
MAX_LINES = 5000


class JobBusy(Exception):
    pass


class Jobs:
    def __init__(self):
        self._lock = threading.Lock()
        self._jobs: dict[str, dict] = {}
        self._running: str | None = None

    def start(self, argv: list[str], cwd: Path, label: str) -> str:
        with self._lock:
            if self._running:
                raise JobBusy(self._running)
            job_id = uuid.uuid4().hex[:10]
            self._jobs[job_id] = {"id": job_id, "label": label, "status": "running",
                                  "exit_code": None, "lines": [], "dropped": 0}
            self._running = job_id
        threading.Thread(target=self._run, args=(job_id, argv, cwd), daemon=True).start()
        return job_id

    def _run(self, job_id, argv, cwd):
        job = self._jobs[job_id]
        try:
            proc = subprocess.Popen(
                argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                env={**os.environ, "PYTHONUNBUFFERED": "1"})
            for line in proc.stdout:
                job["lines"].append(ANSI.sub("", line.rstrip("\n")))
                if len(job["lines"]) > MAX_LINES:
                    del job["lines"][0]
                    job["dropped"] += 1
            code = proc.wait()
        except OSError as e:
            job["lines"].append(f"could not start: {e}")
            code = 127
        job["exit_code"] = code
        with self._lock:
            self._running = None
        job["status"] = "ok" if code == 0 else "failed"

    def get(self, job_id: str, since: int = 0) -> dict | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        lines = list(job["lines"])
        offset = job["dropped"]
        return {"id": job["id"], "label": job["label"], "status": job["status"],
                "exit_code": job["exit_code"], "lines": lines[max(0, since - offset):],
                "next": offset + len(lines)}

    def current(self) -> dict | None:
        return self.get(self._running) if self._running else None
