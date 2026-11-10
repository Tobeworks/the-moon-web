import subprocess

import pytest

from studio.gitops import commit_releases, releases_dirty


def git(cfg, *args):
    return subprocess.run(["git", "-C", str(cfg.web_root), *args], capture_output=True,
                          text=True, check=True).stdout


@pytest.fixture
def repo(studio_env):
    git(studio_env, "init", "-q", "-b", "main")
    git(studio_env, "config", "user.name", "t")
    git(studio_env, "config", "user.email", "t@example.com")
    git(studio_env, "add", "data/releases.json")
    git(studio_env, "commit", "-q", "-m", "init")
    return studio_env


def test_clean_repo_is_not_dirty_and_commit_refuses(repo):
    assert releases_dirty(repo) is False
    with pytest.raises(ValueError):
        commit_releases(repo, "feat: x")


def test_commit_only_releases_json_and_keeps_other_staged_files(repo):
    repo.releases_path.write_text(repo.releases_path.read_text() + "\n")
    (repo.web_root / "other.txt").write_text("x")
    git(repo, "add", "other.txt")
    assert releases_dirty(repo) is True
    sha = commit_releases(repo, "feat: tmr-099 release")
    assert git(repo, "log", "-1", "--format=%s").strip() == "feat: tmr-099 release"
    assert git(repo, "show", "--name-only", "--format=", "HEAD").split() == ["data/releases.json"]
    assert "A  other.txt" in git(repo, "status", "--short")
    assert git(repo, "rev-parse", "--short", "HEAD").strip() == sha
    assert releases_dirty(repo) is False


def test_empty_message_refused(repo):
    repo.releases_path.write_text(repo.releases_path.read_text() + "\n")
    with pytest.raises(ValueError):
        commit_releases(repo, "  ")


def test_not_a_repo_is_not_dirty(studio_env):
    assert releases_dirty(studio_env) is False
