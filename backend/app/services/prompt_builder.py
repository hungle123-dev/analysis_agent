from __future__ import annotations

import json
from typing import Any

from backend.app.schemas import CreateProposalRequest, DatasetContext

ALLOWED_LIBRARIES = [
    "pandas",
    "numpy",
    "matplotlib",
    "matplotlib.dates",
    "matplotlib.ticker",
    "seaborn",
    "math",
    "statistics",
    "datetime",
    "collections",
]

PROPOSAL_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "code", "explanation", "assumptions", "risk_flags", "expected_outputs"],
    "properties": {
        "summary": {"type": "string", "minLength": 1},
        "code": {"type": "string", "minLength": 1},
        "explanation": {"type": "string", "minLength": 1},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "risk_flags": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "changes_dtype",
                    "creates_chart_file",
                    "creates_table_file",
                    "creates_table_stdout",
                    "drops_rows",
                    "filters_outliers",
                    "needs_human_check",
                    "uses_statistical_model",
                ],
            },
        },
        "expected_outputs": {
            "type": "array",
            "items": {"type": "string", "enum": ["text", "table", "chart", "log"]},
        },
    },
}

SYSTEM_PROMPT = """Ban la AI ho tro phan tich du lieu trong mot ung dung local.

Vai tro cua ban:
- De xuat huong phan tich khi nguoi dung chua ro nen lam gi.
- Tao code Python phan tich du lieu theo yeu cau cua nguoi dung.
- Giai thich code va ket qua dua tren du lieu/artifact he thong cung cap.

Quy tac bat buoc:
- Khong duoc thuc thi code.
- Khong duoc tu y them so lieu, ten cot, hinh anh, bieu do hoac ket qua khong co trong context.
- Khong duoc ket luan bang so lieu neu chua co ket qua thuc thi/artifact.
- Code Python phai gia dinh dataframe dau vao ten la df.
- Truoc khi bien doi du lieu, code phai tao ban sao: work_df = df.copy().
- Khong duoc sua df goc, khong duoc ghi de dataset goc.
- Chi duoc ghi output vao outputs_dir bang dang: outputs_dir / "ten_file.ext"; khong dung thu muc con, "..", absolute path.
- Co the gan bien trung gian an toan: chart_path = outputs_dir / "chart.png"; sau do plt.savefig(chart_path).
- Duoi file output nen dung dung loai: chart .png/.jpg/.jpeg/.svg/.webp/.pdf; bang .csv/.xlsx/.html/.json/.md/.parquet; text .txt/.log/.md/.json.
- Khong dung open()/write() tru khi that su can file text; uu tien print() de hien thi nhan xet va DataFrame.to_csv(...) de luu bang.
- Khong duoc doc file khac, goi shell, goi network, import module nguy hiem.
- Moi khoi code quan trong phai co comment tieng Viet giai thich thao tac.
- Tra ve duy nhat JSON dung schema, khong boc markdown, khong them van ban ben ngoai JSON.
"""


def build_proposal_messages(payload: CreateProposalRequest, context: DatasetContext) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(payload, context)},
    ]


def build_user_prompt(payload: CreateProposalRequest, context: DatasetContext) -> str:
    prompt_payload = {
        "task": "Create an AI proposal for a human-in-the-loop data analysis workflow.",
        "mode": payload.mode,
        "user_request": payload.user_request,
        "dataset_context": serialize_dataset_context(context),
        "allowed_libraries": ALLOWED_LIBRARIES,
        "runtime_contract": {
            "input_dataframe_name": "df",
            "output_directory_variable": "outputs_dir",
            "must_copy_dataframe_before_mutation": "work_df = df.copy()",
            "execution": "The backend will show code to the user first. Execution happens only after approval.",
        },
        "response_schema": PROPOSAL_JSON_SCHEMA,
    }
    return json.dumps(prompt_payload, ensure_ascii=True, indent=2, default=str)


def serialize_dataset_context(context: DatasetContext) -> dict[str, Any]:
    return {
        "dataset_id": context.id,
        "name": context.name,
        "row_count": context.rows,
        "status": context.status,
        "columns": [
            {
                "name": column.name,
                "dtype": column.dtype,
                "nullable_count": column.nullable_count,
                "sample_values": column.sample_values,
            }
            for column in context.columns
        ],
    }


def render_schema_for_docs() -> str:
    return json.dumps(PROPOSAL_JSON_SCHEMA, ensure_ascii=True, indent=2)
