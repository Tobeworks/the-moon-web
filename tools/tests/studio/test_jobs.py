import sys
import time

import pytest

from studio.jobs import JobBusy, Jobs


def py(code):
    return [sys.executable, "-c", code]


def wait(jobs, job_id, timeout=5):
    end = time.time() + timeout
    while time.time() < end:
        j = jobs.get(job_id)
        if j["status"] != "running":
            return j
        time.sleep(0.02)
    raise AssertionError("job did not finish")


def test_job_collects_lines_and_exit_ok(tmp_path):
    jobs = Jobs()
    j = wait(jobs, jobs.start(py("print('a'); print('b')"), tmp_path, "t"))
    assert j["status"] == "ok" and j["lines"] == ["a", "b"] and j["next"] == 2


def test_failed_exit_code(tmp_path):
    jobs = Jobs()
    j = wait(jobs, jobs.start(py("import sys; sys.exit(3)"), tmp_path, "t"))
    assert j["status"] == "failed" and j["exit_code"] == 3


def test_ansi_is_stripped(tmp_path):
    jobs = Jobs()
    j = wait(jobs, jobs.start(py(r"print('\x1b[32m✓\x1b[0m ok')"), tmp_path, "t"))
    assert j["lines"] == ["✓ ok"]


def test_second_job_is_busy(tmp_path):
    jobs = Jobs()
    first = jobs.start(py("import time; time.sleep(0.5)"), tmp_path, "slow")
    with pytest.raises(JobBusy):
        jobs.start(py("print(1)"), tmp_path, "t")
    assert jobs.current()["id"] == first
    wait(jobs, first)
    assert jobs.current() is None


def test_cancel_stops_running_job(tmp_path):
    jobs = Jobs()
    job_id = jobs.start(py("import time; time.sleep(30)"), tmp_path, "slow")
    time.sleep(0.2)
    assert jobs.cancel(job_id) is True
    assert wait(jobs, job_id)["status"] == "cancelled"
    assert jobs.cancel(job_id) is False
    assert jobs.current() is None


def test_since_returns_only_new_lines(tmp_path):
    jobs = Jobs()
    j = wait(jobs, jobs.start(py("print('a'); print('b'); print('c')"), tmp_path, "t"))
    again = jobs.get(j["id"], since=2)
    assert again["lines"] == ["c"] and again["next"] == 3
    assert jobs.get("nope") is None
