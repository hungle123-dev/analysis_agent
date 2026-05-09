from __future__ import annotations

import json
import os
import time
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError

from backend.app.core.env import load_local_env
from backend.app.schemas import CreateProposalRequest, DatasetContext
from backend.app.services.llm_provider import ProposalDraft
from backend.app.services.prompt_builder import PROPOSAL_JSON_SCHEMA, build_proposal_messages


class DeepSeekLLMProvider:
    name = "deepseek"

    def __init__(self) -> None:
        load_local_env()
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("Missing DEEPSEEK_API_KEY for AI_PROVIDER=deepseek/openai_compatible")

        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash-nothinking").strip()
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip().rstrip("/")
        try:
            # Default generous for OpenAI-compatible local proxies (e.g. ds2api) often ~60s latency.
            timeout = max(5.0, float(os.getenv("DEEPSEEK_TIMEOUT_SECONDS", "120")))
        except ValueError:
            timeout = 120.0
        self.base_url = _normalize_openai_base_url(base_url)
        self.max_tokens = _parse_optional_int_env("DEEPSEEK_MAX_TOKENS", default=2200, minimum=512)
        self.temperature = _parse_float_env("DEEPSEEK_TEMPERATURE", default=0.2, minimum=0.0, maximum=2.0)
        self.extra_body = _build_extra_body()
        self.client = OpenAI(api_key=api_key, base_url=self.base_url, timeout=timeout)

    def create_proposal(self, payload: CreateProposalRequest, context: DatasetContext) -> ProposalDraft:
        messages = build_proposal_messages(payload, context)
        started = time.perf_counter()
        try:
            completion = self.client.chat.completions.create(**self._request_args(messages))
        except RateLimitError as exc:
            raise RuntimeError("DeepSeek rate limit reached. Please retry in a moment.") from exc
        except APITimeoutError as exc:
            raise RuntimeError("DeepSeek request timed out. Please retry.") from exc
        except APIConnectionError as exc:
            raise RuntimeError("Cannot connect to DeepSeek API. Check your network/base URL.") from exc
        except APIStatusError as exc:
            raise RuntimeError(f"DeepSeek API error ({exc.status_code}).") from exc

        duration_ms = int((time.perf_counter() - started) * 1000)
        choice = completion.choices[0]
        finish_reason = getattr(choice, "finish_reason", None)
        if finish_reason == "length":
            raise RuntimeError("DeepSeek response was cut off by max_tokens. Increase DEEPSEEK_MAX_TOKENS.")

        raw_content = choice.message.content or ""
        parsed = _parse_json_content(raw_content)
        return _build_draft(parsed, metadata=self._metadata(completion, duration_ms, finish_reason, messages))

    def _request_args(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        args: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": message["role"], "content": message["content"]} for message in messages],
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
        }
        if self.max_tokens is not None:
            args["max_tokens"] = self.max_tokens
        if self.extra_body:
            args["extra_body"] = self.extra_body
        return args

    def _metadata(self, completion: Any, duration_ms: int, finish_reason: str | None, messages: list[dict[str, str]]) -> dict[str, Any]:
        usage = getattr(completion, "usage", None)
        usage_data = usage.model_dump(mode="json") if hasattr(usage, "model_dump") else {}
        return {
            "provider": self.name,
            "base_url": self.base_url,
            "model": getattr(completion, "model", self.model),
            "configured_model": self.model,
            "finish_reason": finish_reason,
            "llm_duration_ms": duration_ms,
            "prompt_chars": sum(len(message["content"]) for message in messages),
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "extra_body": self.extra_body,
            "usage": usage_data,
        }


def _normalize_openai_base_url(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    if not value:
        return "https://api.deepseek.com/v1"

    append_v1 = os.getenv("DEEPSEEK_APPEND_V1", "true").strip().lower() in {"1", "true", "yes", "on"}
    terminal_paths = ("/v1", "/beta", "/anthropic")
    if not append_v1 or value.endswith(terminal_paths):
        return value
    return f"{value}/v1"


def _parse_optional_int_env(name: str, default: int | None, minimum: int) -> int | None:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    if raw.strip().lower() in {"none", "null", "off", "false"}:
        return None
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


def _parse_float_env(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        return default
    return min(max(value, minimum), maximum)


def _build_extra_body() -> dict[str, Any]:
    extra_body: dict[str, Any] = {}
    raw_json = os.getenv("DEEPSEEK_EXTRA_BODY_JSON", "").strip()
    if raw_json:
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise RuntimeError("DEEPSEEK_EXTRA_BODY_JSON must be valid JSON") from exc
        if not isinstance(parsed, dict):
            raise RuntimeError("DEEPSEEK_EXTRA_BODY_JSON must be a JSON object")
        extra_body.update(parsed)

    thinking = os.getenv("DEEPSEEK_THINKING", "").strip().lower()
    if thinking in {"enabled", "disabled"}:
        extra_body.setdefault("thinking", {"type": thinking})
    return extra_body


def _parse_json_content(raw_content: str) -> dict[str, Any]:
    text = raw_content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"DeepSeek returned invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("DeepSeek response must be a JSON object")
    return data


def _build_draft(data: dict[str, Any], metadata: dict[str, Any] | None = None) -> ProposalDraft:
    required_fields = PROPOSAL_JSON_SCHEMA["required"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise RuntimeError(f"DeepSeek response missing required fields: {', '.join(missing_fields)}")

    risk_flags = data.get("risk_flags", [])
    expected_outputs = data.get("expected_outputs", [])
    assumptions = data.get("assumptions", [])

    valid_risk_flags = set(PROPOSAL_JSON_SCHEMA["properties"]["risk_flags"]["items"]["enum"])
    valid_expected_outputs = set(PROPOSAL_JSON_SCHEMA["properties"]["expected_outputs"]["items"]["enum"])

    return ProposalDraft(
        summary=str(data.get("summary", "")).strip(),
        code=str(data.get("code", "")).strip(),
        explanation=str(data.get("explanation", "")).strip(),
        assumptions=[str(item) for item in assumptions if str(item).strip()],
        risk_flags=[str(item) for item in risk_flags if str(item) in valid_risk_flags],
        expected_outputs=[str(item) for item in expected_outputs if str(item) in valid_expected_outputs],
        metadata=metadata or {},
    )
