from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Protocol

from backend.app.core.env import load_local_env
from backend.app.schemas import CreateProposalRequest, DatasetContext


@dataclass(frozen=True)
class ProposalDraft:
    summary: str
    code: str
    explanation: str
    assumptions: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMProvider(Protocol):
    name: str

    def create_proposal(self, payload: CreateProposalRequest, context: DatasetContext) -> ProposalDraft:
        """Return a structured proposal without executing any generated code."""


def get_llm_provider() -> LLMProvider:
    load_local_env()
    provider_name = os.getenv("AI_PROVIDER", "mock").strip().lower()
    if provider_name == "mock":
        from backend.app.services.mock_llm_provider import MockLLMProvider

        return MockLLMProvider()
    if provider_name in {"deepseek", "openai_compatible"}:
        from backend.app.services.deepseek_llm_provider import DeepSeekLLMProvider

        return DeepSeekLLMProvider()

    raise RuntimeError(
        f"Unsupported AI_PROVIDER={provider_name!r}. "
        "Use 'mock', 'deepseek', or 'openai_compatible', or add a provider adapter that implements LLMProvider."
    )
