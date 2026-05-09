from __future__ import annotations

from backend.app.services.deepseek_llm_provider import (
    _build_extra_body,
    _normalize_openai_base_url,
    _parse_optional_int_env,
)


def test_normalize_base_url_appends_v1_by_default(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_APPEND_V1", raising=False)

    assert _normalize_openai_base_url("http://127.0.0.1:5001") == "http://127.0.0.1:5001/v1"


def test_normalize_base_url_does_not_duplicate_v1(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_APPEND_V1", raising=False)

    assert _normalize_openai_base_url("http://127.0.0.1:5001/v1") == "http://127.0.0.1:5001/v1"


def test_normalize_base_url_can_disable_v1_append(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_APPEND_V1", "false")

    assert _normalize_openai_base_url("https://api.deepseek.com") == "https://api.deepseek.com"


def test_parse_max_tokens_supports_none_and_minimum(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_MAX_TOKENS", "none")
    assert _parse_optional_int_env("DEEPSEEK_MAX_TOKENS", default=2200, minimum=512) is None

    monkeypatch.setenv("DEEPSEEK_MAX_TOKENS", "100")
    assert _parse_optional_int_env("DEEPSEEK_MAX_TOKENS", default=2200, minimum=512) == 512


def test_extra_body_merges_json_and_thinking(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_EXTRA_BODY_JSON", '{"custom": true}')
    monkeypatch.setenv("DEEPSEEK_THINKING", "disabled")

    assert _build_extra_body() == {"custom": True, "thinking": {"type": "disabled"}}
