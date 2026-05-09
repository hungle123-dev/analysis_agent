from __future__ import annotations

import os
import sys

from backend.app.core.env import load_local_env
from backend.app.schemas import CreateProposalRequest
from backend.app.services.dataset_service import get_dataset_context
from backend.app.services.deepseek_llm_provider import DeepSeekLLMProvider


def main() -> int:
    load_local_env()
    dataset_id = os.getenv("LLM_TEST_DATASET_ID", "vietnam_real_estate_cleaned")
    request_text = os.getenv(
        "LLM_TEST_REQUEST",
        "Tinh gia trung binh theo tinh thanh va ve bieu do cot top 10.",
    )

    provider = DeepSeekLLMProvider()
    context = get_dataset_context(dataset_id)
    payload = CreateProposalRequest(dataset_id=dataset_id, user_request=request_text)

    print(f"provider={provider.name}")
    print(f"base_url={provider.base_url}")
    print(f"model={provider.model}")
    print(f"max_tokens={provider.max_tokens}")
    print(f"extra_body={provider.extra_body}")

    draft = provider.create_proposal(payload, context)
    print(f"summary={draft.summary}")
    print(f"code_chars={len(draft.code)}")
    print(f"explanation_chars={len(draft.explanation)}")
    print(f"metadata={draft.metadata}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"LLM provider test failed: {exc}", file=sys.stderr)
        raise
