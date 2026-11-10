from types import SimpleNamespace

import anthropic
import httpx
import pytest

from studio import ai
from studio.config import Config

RELEASE = {"artist": "Logic Moon", "title": "Perihelion Drift", "format": "EP", "genre": "Dark Ambient",
           "release_date": "2026-11-13",
           "tracks": [{"number": 1, "title": "Perihelion Drift", "duration": "7:12"},
                      {"number": 2, "title": "Velum", "duration": "5:57"}]}


class FakeClient:
    def __init__(self, text="A calm text.", stop_reason="end_turn", error=None):
        self.calls, self.text, self.stop_reason, self.error = [], text, stop_reason, error
        self.messages = self

    def create(self, **kw):
        self.calls.append(kw)
        if self.error:
            raise self.error
        return SimpleNamespace(stop_reason=self.stop_reason,
                               content=[SimpleNamespace(type="text", text=self.text)])


@pytest.fixture
def cfg(tmp_path):
    return Config(web_root=tmp_path, assets_dir=tmp_path, scraper_dir=tmp_path)


def test_prompt_contains_facts_notes_draft_and_examples():
    p = ai.build_prompt(RELEASE, "rain, orbital mechanics", "My draft.", ["Old text one.", "Old text two."])
    for needle in ("Logic Moon", "Perihelion Drift", "1. Perihelion Drift (7:12)", "2. Velum (5:57)",
                   "Dark Ambient", "rain, orbital mechanics", "My draft.", "Old text one.", "Old text two."):
        assert needle in p


def test_prompt_without_optional_parts():
    p = ai.build_prompt(RELEASE, " ", "", [])
    assert "keywords" not in p and "Current draft" not in p and "Older release texts" not in p


def test_generate_returns_stripped_text_and_sends_system_prompt(cfg):
    client = FakeClient("  Text.\n")
    assert ai.generate_about(cfg, RELEASE, client=client) == "Text."
    call = client.calls[0]
    assert call["model"] == ai.MODEL and "Do not invent" in call["system"]


def test_refusal_and_empty_text_raise(cfg):
    with pytest.raises(ai.AiError):
        ai.generate_about(cfg, RELEASE, client=FakeClient(stop_reason="refusal"))
    with pytest.raises(ai.AiError):
        ai.generate_about(cfg, RELEASE, client=FakeClient(text="  "))


def test_auth_error_is_translated(cfg):
    resp = httpx.Response(401, request=httpx.Request("POST", "http://x"))
    err = anthropic.AuthenticationError("bad key", response=resp, body=None)
    with pytest.raises(ai.AiError, match="abgelehnt"):
        ai.generate_about(cfg, RELEASE, client=FakeClient(error=err))


def test_ready_reads_env_file_and_environment(cfg, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert ai.ready(cfg) is False
    (cfg.web_root / ".env").write_text("# ANTHROPIC_API_KEY=commented\nANTHROPIC_API_KEY=sk-test # note\n")
    assert ai.ready(cfg) is True
    assert ai._env(cfg)["ANTHROPIC_API_KEY"] == "sk-test"


def test_no_key_without_client_raises(cfg, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ai.AiError, match="ANTHROPIC_API_KEY"):
        ai.generate_about(cfg, RELEASE)
