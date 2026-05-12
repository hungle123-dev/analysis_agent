from __future__ import annotations

from backend.app.services.deepseek_llm_provider import (
    _build_extra_body,
    _build_extra_headers,
    _build_execution_insight_messages,
    _normalize_openai_base_url,
    _parse_optional_int_env,
)
from backend.app.services.llm_provider import ExecutionInsightInput


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


def test_extra_headers_support_ds2api_target_account(monkeypatch):
    monkeypatch.setenv("DS2API_TARGET_ACCOUNT", "student@example.com")
    monkeypatch.delenv("DEEPSEEK_TARGET_ACCOUNT", raising=False)

    assert _build_extra_headers() == {"X-Ds2-Target-Account": "student@example.com"}


def test_extra_headers_support_legacy_deepseek_target_account(monkeypatch):
    monkeypatch.delenv("DS2API_TARGET_ACCOUNT", raising=False)
    monkeypatch.setenv("DEEPSEEK_TARGET_ACCOUNT", "backup@example.com")

    assert _build_extra_headers() == {"X-Ds2-Target-Account": "backup@example.com"}


def test_execution_insight_messages_are_text_only_and_grounded_in_local_outputs():
    messages = _build_execution_insight_messages(
        ExecutionInsightInput(
            user_request="Ve bieu do doanh thu",
            code="print('x')",
            stdout="month revenue\n2025-01 100",
            stderr="",
            artifacts=[{"type": "chart", "name": "chart.png", "path": "runs/run_x/outputs/chart.png"}],
            table_previews=[{"name": "summary.csv", "preview": "month,revenue\n2025-01,100"}],
        )
    )

    content = messages[0]["content"]
    assert isinstance(content, str)
    assert "EVIDENCE" in content
    assert "stdout" in content.lower()
    assert "Preview bảng kết quả" in content
    assert "Hình ảnh/biểu đồ chỉ là minh họa" in content
    assert "print('x')" not in content
    assert "image_url" not in content
