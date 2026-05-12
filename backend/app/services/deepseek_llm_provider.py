from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from backend.app.core.env import load_local_env
from backend.app.schemas import CreateProposalRequest, DatasetContext
from backend.app.services.llm_provider import ExecutionInsightDraft, ExecutionInsightInput, ProposalDraft
from backend.app.services.prompt_builder import PROPOSAL_JSON_SCHEMA, build_proposal_messages


class DeepSeekLLMProvider:
    name = "deepseek"

    def __init__(self) -> None:
        load_local_env()
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("Missing DEEPSEEK_API_KEY for AI_PROVIDER=deepseek/openai_compatible")

        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash-nothinking").strip()
        self.insight_model = os.getenv("DEEPSEEK_INSIGHT_MODEL", self.model).strip() or self.model
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip().rstrip("/")
        try:
            # Default generous for OpenAI-compatible local proxies (e.g. ds2api) often ~60s latency.
            timeout = max(5.0, float(os.getenv("DEEPSEEK_TIMEOUT_SECONDS", "120")))
        except ValueError:
            timeout = 120.0
        try:
            insight_timeout = max(3.0, float(os.getenv("AI_EXPLAIN_RESULT_TIMEOUT_SECONDS", "45")))
        except ValueError:
            insight_timeout = 45.0
        self.timeout = timeout
        self.base_url = _normalize_openai_base_url(base_url)
        self.max_tokens = _parse_optional_int_env("DEEPSEEK_MAX_TOKENS", default=2200, minimum=512)
        self.insight_max_tokens = _parse_optional_int_env("DEEPSEEK_INSIGHT_MAX_TOKENS", default=900, minimum=256)
        self.temperature = _parse_float_env("DEEPSEEK_TEMPERATURE", default=0.2, minimum=0.0, maximum=2.0)
        self.extra_body = _build_extra_body()
        self.extra_headers = _build_extra_headers()
        self.insight_timeout = insight_timeout
        self.api_key = api_key

    def create_proposal(self, payload: CreateProposalRequest, context: DatasetContext) -> ProposalDraft:
        messages = build_proposal_messages(payload, context)
        started = time.perf_counter()
        completion = self._post_chat_completion(self._request_args(messages), timeout=self.timeout)
        duration_ms = int((time.perf_counter() - started) * 1000)
        choice = completion["choices"][0]
        finish_reason = choice.get("finish_reason")
        if finish_reason == "length":
            raise RuntimeError("DeepSeek response was cut off by max_tokens. Increase DEEPSEEK_MAX_TOKENS.")

        raw_content = choice.get("message", {}).get("content") or ""
        parsed = _parse_json_content(raw_content)
        return _build_draft(parsed, metadata=self._metadata(completion, duration_ms, finish_reason, messages))

    def explain_execution_result(self, payload: ExecutionInsightInput) -> ExecutionInsightDraft:
        messages = _build_execution_insight_messages(payload)
        started = time.perf_counter()
        completion = self._post_chat_completion(
            {
                "model": self.insight_model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": self.insight_max_tokens,
            },
            timeout=self.insight_timeout,
        )
        duration_ms = int((time.perf_counter() - started) * 1000)
        choice = completion["choices"][0]
        raw_content = (choice.get("message", {}).get("content") or "").strip()
        if not raw_content:
            raise RuntimeError("DeepSeek returned empty execution insight.")
        return ExecutionInsightDraft(
            insight=raw_content,
            metadata={
                "provider": self.name,
                "model": completion.get("model", self.insight_model),
                "configured_model": self.insight_model,
                "finish_reason": choice.get("finish_reason"),
                "llm_duration_ms": duration_ms,
                "timeout_seconds": self.insight_timeout,
                "prompt_chars": _message_text_chars(messages),
                "used_table_previews": len(payload.table_previews),
                "target_account": self.extra_headers.get("X-Ds2-Target-Account") if self.extra_headers else "",
                "usage": completion.get("usage", {}),
            },
        )

    def _request_args(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        args: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": message["role"], "content": message["content"]} for message in messages],
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
        }
        if self.extra_headers:
            args["extra_headers"] = self.extra_headers
        if self.max_tokens is not None:
            args["max_tokens"] = self.max_tokens
        if self.extra_body:
            args["extra_body"] = self.extra_body
        return args

    def _post_chat_completion(self, args: dict[str, Any], *, timeout: float) -> dict[str, Any]:
        body = {key: value for key, value in args.items() if key not in {"extra_headers", "extra_body"}}
        extra_body = args.get("extra_body")
        if isinstance(extra_body, dict):
            body.update(extra_body)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8",
        }
        headers.update(args.get("extra_headers") or {})

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        request = urllib.request.Request(
            url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                parsed = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = _read_http_error(exc)
            if exc.code == 429:
                raise RuntimeError(f"DeepSeek rate limit reached: {detail}") from exc
            raise RuntimeError(f"DeepSeek API error ({exc.code}): {detail}") from exc
        except TimeoutError as exc:
            raise RuntimeError("DeepSeek request timed out. Please retry.") from exc
        except (urllib.error.URLError, OSError) as exc:
            raise RuntimeError(f"Cannot connect to DeepSeek API. Check your network/base URL: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("DeepSeek returned invalid JSON transport response.") from exc

        if not isinstance(parsed, dict):
            raise RuntimeError("DeepSeek response must be a JSON object")
        return parsed

    def _metadata(self, completion: dict[str, Any], duration_ms: int, finish_reason: str | None, messages: list[dict[str, str]]) -> dict[str, Any]:
        return {
            "provider": self.name,
            "base_url": self.base_url,
            "model": completion.get("model", self.model),
            "configured_model": self.model,
            "finish_reason": finish_reason,
            "llm_duration_ms": duration_ms,
            "prompt_chars": sum(len(message["content"]) for message in messages),
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "extra_body": self.extra_body,
            "target_account": self.extra_headers.get("X-Ds2-Target-Account") if self.extra_headers else "",
            "usage": completion.get("usage", {}),
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


def _build_extra_headers() -> dict[str, str]:
    target_account = (
        os.getenv("DS2API_TARGET_ACCOUNT", "").strip()
        or os.getenv("DEEPSEEK_TARGET_ACCOUNT", "").strip()
    )
    if not target_account:
        return {}
    return {"X-Ds2-Target-Account": target_account}


def _read_http_error(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        return str(exc.reason or exc)
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return body[:1000]
    if isinstance(parsed, dict):
        message = parsed.get("error", {}).get("message") if isinstance(parsed.get("error"), dict) else None
        return str(message or parsed)[:1000]
    return str(parsed)[:1000]


def _build_execution_insight_messages(payload: ExecutionInsightInput) -> list[dict[str, Any]]:
    artifact_summary = [
        {"name": item.get("name"), "type": item.get("type"), "path": item.get("path")}
        for item in payload.artifacts
    ]
    text_parts = [
        "Bạn là AI hỗ trợ phân tích dữ liệu sau khi code đã chạy local.",
        "Nhiệm vụ: nhận xét kết quả bằng tiếng Việt dựa trên số liệu thật sau execution.",
        "Chỉ được nhận xét dựa trên EVIDENCE gồm stdout, bảng preview và metadata artifact thật bên dưới.",
        "Không được bịa thêm số liệu, cột dữ liệu, địa danh, nhóm dữ liệu, kết quả hoặc kết luận không có trong EVIDENCE.",
        "Không được nhắc tên riêng/địa danh/nhóm dữ liệu nếu chuỗi đó không xuất hiện nguyên văn trong EVIDENCE.",
        "Không được viết kiểu 'A không có trong top' nếu A không xuất hiện trong EVIDENCE.",
        "Hình ảnh/biểu đồ chỉ là minh họa giao diện; không dùng ảnh làm nguồn số liệu chính.",
        "Nếu stdout/bảng preview không đủ dữ liệu để trả lời một phần câu hỏi, hãy nói rõ phần thiếu thay vì đoán.",
        "Mỗi bullet phải gắn với ít nhất một số liệu hoặc tên nhóm xuất hiện trong EVIDENCE.",
        "Trả lời 3-5 bullet ngắn gọn, tập trung vào: kết luận chính, số liệu nổi bật, điểm bất thường, và điều người dùng nên kiểm tra tiếp.",
        "",
        f"Yêu cầu ban đầu của người dùng: {payload.user_request}",
        "",
        "EVIDENCE - Danh sách artifact:",
        json.dumps(artifact_summary, ensure_ascii=False),
        "",
        "EVIDENCE - Stdout từ code local:",
        payload.stdout[:6000] or "(Không có stdout)",
    ]
    if payload.stderr.strip():
        text_parts.extend(["", "EVIDENCE - Stderr:", payload.stderr[:2000]])
    if payload.table_previews:
        text_parts.extend(["", "EVIDENCE - Preview bảng kết quả:"])
        text_parts.append(json.dumps(payload.table_previews, ensure_ascii=False))

    return [{"role": "user", "content": "\n".join(text_parts)}]


def _message_text_chars(messages: list[dict[str, Any]]) -> int:
    total = 0
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, str):
            total += len(content)
        elif isinstance(content, list):
            total += sum(len(item.get("text", "")) for item in content if item.get("type") == "text")
    return total


def _usage_to_dict(usage: Any) -> dict[str, Any]:
    return usage.model_dump(mode="json") if hasattr(usage, "model_dump") else {}


def _parse_json_content(raw_content: str) -> dict[str, Any]:
    text = raw_content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    if not text.startswith("{"):
        text = _extract_json_object(text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        snippet = raw_content.strip().replace("\n", " ")[:240]
        raise RuntimeError(f"DeepSeek trả về JSON không hợp lệ: {exc}. Phần đầu phản hồi: {snippet}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("DeepSeek phải trả về một JSON object.")
    return data


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def _build_draft(data: dict[str, Any], metadata: dict[str, Any] | None = None) -> ProposalDraft:
    required_fields = PROPOSAL_JSON_SCHEMA["required"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise RuntimeError(f"DeepSeek response missing required fields: {', '.join(missing_fields)}")

    risk_flags = _coerce_string_list(data.get("risk_flags", []))
    expected_outputs = _coerce_string_list(data.get("expected_outputs", []))
    assumptions = _coerce_string_list(data.get("assumptions", []))

    valid_risk_flags = set(PROPOSAL_JSON_SCHEMA["properties"]["risk_flags"]["items"]["enum"])
    valid_expected_outputs = set(PROPOSAL_JSON_SCHEMA["properties"]["expected_outputs"]["items"]["enum"])

    return ProposalDraft(
        summary=str(data.get("summary", "")).strip(),
        code=str(data.get("code", "")).strip(),
        explanation=str(data.get("explanation", "")).strip(),
        assumptions=[item for item in assumptions if item.strip()],
        risk_flags=[str(item) for item in risk_flags if str(item) in valid_risk_flags],
        expected_outputs=[str(item) for item in expected_outputs if str(item) in valid_expected_outputs],
        metadata=metadata or {},
    )


def _coerce_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []
