from __future__ import annotations

import json

from backend.app.schemas import ColumnInfo, CreateProposalRequest, DatasetContext
from backend.app.services.prompt_builder import build_proposal_messages


def test_prompt_builder_includes_dataset_context_and_schema():
    context = DatasetContext(
        id="sales_2025",
        name="sales_2025.csv",
        rows=4,
        status="ready",
        columns=[
            ColumnInfo(name="date", dtype="object", nullable_count=0, sample_values=["2025-01-05"]),
            ColumnInfo(name="revenue", dtype="int64", nullable_count=0, sample_values=[1240000]),
        ],
    )
    payload = CreateProposalRequest(dataset_id="sales_2025", user_request="Ve doanh thu theo thang")

    messages = build_proposal_messages(payload, context)

    assert messages[0]["role"] == "system"
    assert "Khong duoc thuc thi code" in messages[0]["content"]
    assert "work_df = df.copy()" in messages[0]["content"]

    user_payload = json.loads(messages[1]["content"])
    assert user_payload["user_request"] == "Ve doanh thu theo thang"
    assert user_payload["dataset_context"]["dataset_id"] == "sales_2025"
    assert user_payload["dataset_context"]["columns"][1]["name"] == "revenue"
    assert "code" in user_payload["response_schema"]["required"]
    assert user_payload["runtime_contract"]["output_directory_variable"] == "outputs_dir"
