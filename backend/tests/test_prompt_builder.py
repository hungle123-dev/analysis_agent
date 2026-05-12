from __future__ import annotations

import json

from backend.app.schemas import ColumnInfo, CreateProposalRequest, DatasetContext
from backend.app.services.prompt_builder import PROMPT_VERSION, build_proposal_messages


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
    assert "Không được thực thi code" in messages[0]["content"]
    assert "work_df = df.copy()" in messages[0]["content"]
    assert "Chỉ được dùng tên cột xuất hiện" in messages[0]["content"]
    assert "Không được giả định các cột" in messages[0]["content"]
    assert "raise ValueError" in messages[0]["content"]
    assert "placeholder" in messages[0]["content"].lower()

    user_payload = json.loads(messages[1]["content"])
    assert user_payload["phien_ban_prompt"] == PROMPT_VERSION
    assert user_payload["yeu_cau_nguoi_dung"] == "Ve doanh thu theo thang"
    assert user_payload["ngu_canh_du_lieu"]["ma_dataset"] == "sales_2025"
    assert user_payload["ngu_canh_du_lieu"]["cac_cot"][1]["ten_cot"] == "revenue"
    assert user_payload["nang_luc_dataset"]["calendar_columns"] == ["date"]
    assert user_payload["nang_luc_dataset"]["numeric_columns"] == ["revenue"]
    assert user_payload["nang_luc_dataset"]["revenue_columns"] == ["revenue"]
    assert user_payload["goi_y_phan_tich_kha_thi"]
    assert len(user_payload["vi_du_dieu_huong"]) >= 2
    assert any(example["expected_outputs"] == ["text"] for example in user_payload["vi_du_dieu_huong"])
    assert "code" in user_payload["schema_phan_hoi_bat_buoc"]["required"]
    assert user_payload["hop_dong_runtime"]["bien_thu_muc_output"] == "outputs_dir"
