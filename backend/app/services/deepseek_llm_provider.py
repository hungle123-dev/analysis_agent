from __future__ import annotations

import json
import os
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError

from backend.app.schemas import CreateProposalRequest, DatasetContext
from backend.app.services.llm_provider import ProposalDraft
from backend.app.services.prompt_builder import PROPOSAL_JSON_SCHEMA, build_proposal_messages


class DeepSeekLLMProvider:
    name = "deepseek"

    def __init__(self) -> None:
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("Missing DEEPSEEK_API_KEY for AI_PROVIDER=deepseek")

        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip().rstrip("/")
        self.client = OpenAI(api_key=api_key, base_url=f"{base_url}/v1")

    def create_proposal(self, payload: CreateProposalRequest, context: DatasetContext) -> ProposalDraft:
        messages = build_proposal_messages(payload, context)
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": message["role"], "content": message["content"]}
                    for message in messages
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
        except RateLimitError as exc:
            raise RuntimeError("DeepSeek rate limit reached. Please retry in a moment.") from exc
        except APITimeoutError as exc:
            raise RuntimeError("DeepSeek request timed out. Please retry.") from exc
        except APIConnectionError as exc:
            raise RuntimeError("Cannot connect to DeepSeek API. Check your network/base URL.") from exc
        except APIStatusError as exc:
            raise RuntimeError(f"DeepSeek API error ({exc.status_code}).") from exc

        raw_content = completion.choices[0].message.content or ""
        parsed = _parse_json_content(raw_content)
        return _build_draft(parsed)


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


def _build_draft(data: dict[str, Any]) -> ProposalDraft:
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
    )
