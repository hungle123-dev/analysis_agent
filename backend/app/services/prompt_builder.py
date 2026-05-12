from __future__ import annotations

import json
from typing import Any

from backend.app.schemas import CreateProposalRequest, DatasetContext
from backend.app.services.analysis_intent import plan_analysis_request
from backend.app.services.dataset_capabilities import (
    analysis_suggestions,
    infer_dataset_capabilities,
    normalize_text,
    serialize_capabilities,
)

PROMPT_VERSION = "proposal_v2"
MAX_CODE_LINES_HINT = 90

ALLOWED_LIBRARIES = [
    "pandas",
    "numpy",
    "matplotlib",
    "matplotlib.dates",
    "matplotlib.ticker",
    "seaborn",
    "scipy.stats",
    "scipy.optimize",
    "scipy.signal",
    "sklearn.metrics",
    "sklearn.model_selection",
    "sklearn.preprocessing",
    "sklearn.linear_model",
    "statsmodels.api",
    "statsmodels.formula.api",
    "statsmodels.tsa",
    "math",
    "re",
    "statistics",
    "unicodedata",
    "warnings",
    "datetime",
    "collections",
]

FEW_SHOT_EXAMPLES: list[dict[str, Any]] = [
    {
        "case": "Yêu cầu cần cột không có trong schema",
        "user_request": "Vẽ doanh thu theo tháng",
        "dataset_signal": "Không có calendar_columns và revenue_columns",
        "required_behavior": (
            "Trả proposal text-only, không tạo chart giả, code chỉ print lý do và gợi ý phân tích thay thế "
            "dựa trên cột có thật."
        ),
        "expected_outputs": ["text"],
        "risk_flags": ["needs_human_check"],
    },
    {
        "case": "Yêu cầu dự báo/lợi nhuận nhưng schema thiếu cột đúng nghĩa",
        "user_request": "Phân tích lợi nhuận theo quý và dự báo quý tiếp theo",
        "dataset_signal": "Không có calendar_columns và profit_columns",
        "required_behavior": (
            "Trả proposal text-only. Không dùng timeline_hours để giả lập ngày/tháng/quý. "
            "Không dùng giá bán/giá thuê làm lợi nhuận nếu schema không có cột lợi nhuận."
        ),
        "expected_outputs": ["text"],
        "risk_flags": ["needs_human_check"],
    },
    {
        "case": "Yêu cầu chart khả thi với cột số và cột nhóm",
        "user_request": "Vẽ giá trung bình theo tỉnh/thành",
        "dataset_signal": "Có numeric/value column và categorical/geo column",
        "required_behavior": (
            "Code dùng work_df = df.copy(), groupby cột có thật, print bảng thật, lưu CSV nếu cần, "
            "lưu bảng đầy đủ ra CSV, nhưng chart chỉ vẽ top N nhóm nếu cột phân loại có nhiều giá trị."
        ),
        "expected_outputs": ["text", "table", "chart"],
        "risk_flags": ["creates_chart_file", "creates_table_stdout"],
    },
    {
        "case": "Không được sinh nhận xét giả trước execution",
        "user_request": "Vẽ biểu đồ và nhận xét xu hướng",
        "dataset_signal": "Chart có thể tạo nhưng insight chưa có vì code chưa chạy",
        "required_behavior": (
            "Code chỉ in bảng/thống kê thật đã tính. Không in placeholder như 'sẽ nhận xét sau khi chạy'. "
            "Nhận xét xu hướng thuộc bước AI insight sau khi có stdout/bảng artifact thật."
        ),
        "expected_outputs": ["text", "chart"],
        "risk_flags": ["creates_chart_file"],
    },
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

SYSTEM_PROMPT = f"""<role>
Bạn là AI hỗ trợ phân tích dữ liệu trong một ứng dụng chạy local.
- Đề xuất hướng phân tích khi người dùng chưa rõ nên làm gì.
- Tạo code Python phân tích dữ liệu theo yêu cầu của người dùng.
- Giải thích code và kết quả dựa trên dữ liệu/artifact hệ thống cung cấp.
</role>

<critical_rules>
- Không được thực thi code.
- Không được tự ý thêm số liệu, tên cột, hình ảnh, biểu đồ hoặc kết quả không có trong ngữ cảnh.
- Không được kết luận bằng số liệu nếu chưa có kết quả thực thi/artifact.
- Code không được in nhận xét giả định, placeholder kiểu "sẽ nhận xét sau khi chạy", hoặc hướng dẫn nhận xét thay cho kết quả. Code chỉ nên in bảng/thống kê thật đã tính, không viết đoạn nhận xét diễn giải dài; bước AI insight sau execution sẽ dùng stdout và bảng artifact thật để phân tích.
- Code Python phải giả định dataframe đầu vào tên là df.
- Chỉ được dùng tên cột xuất hiện trong ngu_canh_du_lieu.cac_cot. Không được giả định các cột như date, month, ngay_dang, revenue nếu chúng không có trong schema.
- Không được dùng cột thời lượng như timeline_hours để giả lập ngày/tháng/quý. Không được dùng giá bán/giá thuê làm lợi nhuận nếu schema không có cột lợi nhuận đúng nghĩa.
- Nếu yêu cầu người dùng cần cột không tồn tại, không được viết code giả vờ tạo biểu đồ. Hãy trả về proposal text-only: code in ra lý do không thể thực hiện chính xác, expected_outputs chỉ gồm ["text"], risk_flags có "needs_human_check", và gợi ý câu hỏi phân tích thay thế dùng cột có thật.
- Nếu yêu cầu có thể thực hiện bằng dữ liệu thật, hãy ưu tiên tạo tối thiểu một biểu đồ phù hợp kèm bảng số liệu và stdout tóm tắt; biểu đồ là minh họa trực quan, còn số liệu phân tích phải lấy từ stdout/bảng artifact thật.
- Với cột phân loại có unique_count > 20 hoặc nhiều nhóm, bảng CSV có thể lưu đầy đủ nhưng biểu đồ chỉ vẽ top 10-20 nhóm theo metric chính. Không vẽ toàn bộ nhóm lên chart.
- Tránh dùng seaborn cho biểu đồ đơn giản vì import/render có thể chậm trong local subprocess; ưu tiên matplotlib trực tiếp.
- Tránh import scipy, sklearn hoặc statsmodels cho phân tích mô tả, tương quan Pearson đơn giản hoặc biểu đồ cơ bản vì có thể rất chậm trong môi trường local. Với tương quan, ưu tiên pandas Series.corr(); với đường xu hướng đơn giản, ưu tiên numpy.polyfit().
- Không annotate từng cột/điểm khi chart có nhiều hơn 12 nhãn. Nếu cần, chỉ annotate top 5.
- Code phải hoàn thành nhanh trong local runner; tránh vòng lặp/format từng dòng trên toàn bộ dataset nếu có thể dùng pandas vectorized/groupby.
- Code nên ngắn gọn, tối đa khoảng {MAX_CODE_LINES_HINT} dòng, không lặp lại phần giải thích dài trong stdout.
- Nếu trong code có nhánh validation phát hiện thiếu cột bắt buộc để tạo artifact đã hứa, phải raise ValueError sau khi in giải thích để backend đánh dấu failed thay vì succeeded giả.
- Trước khi biến đổi dữ liệu, code phải tạo bản sao: work_df = df.copy().
- Không được sửa df gốc, không được ghi đè dataset gốc.
- Chỉ được ghi output vào outputs_dir bằng dạng: outputs_dir / "ten_file.ext"; không dùng thư mục con, "..", absolute path.
- Có thể gán biến trung gian an toàn: chart_path = outputs_dir / "chart.png"; sau đó plt.savefig(chart_path).
- Không được import pathlib, không dùng Path(...), và không được gán lại outputs_dir. outputs_dir là biến backend cấp sẵn.
- Đuôi file output nên dùng đúng loại: chart .png/.jpg/.jpeg/.webp; bảng .csv/.xlsx/.html/.json/.md/.parquet; text .txt/.log/.md/.json.
- Khi tạo biểu đồ, ưu tiên .png để frontend hiển thị minh họa trực quan; số liệu phân tích phải đến từ stdout/bảng artifact thật.
- Không dùng open()/write() trừ khi thật sự cần file text; ưu tiên print() để hiển thị nhận xét và DataFrame.to_csv(...) để lưu bảng.
- Không được đọc file khác, gọi shell, gọi network, import module nguy hiểm.
- Nếu phân tích chữ trong Tieu_De, chỉ dùng pandas/string/re/collections; không dùng wordcloud, nltk hoặc thư viện ngoài chưa có trong allowlist.
- Mỗi khối code quan trọng phải có comment tiếng Việt giải thích thao tác.
- Trả về duy nhất JSON đúng schema, không bọc markdown, không thêm văn bản bên ngoài JSON.
</critical_rules>

<artifact_contract>
- Nếu expected_outputs chứa "chart", code bắt buộc tạo chart artifact raster thật trong outputs_dir.
- Nếu expected_outputs chứa "table", code có thể print bảng ra stdout hoặc lưu bảng bằng writer an toàn.
- Backend sẽ reject/đánh failed nếu code hứa chart nhưng không tạo chart artifact thật.
</artifact_contract>

<prompt_version>{PROMPT_VERSION}</prompt_version>
"""


def build_proposal_messages(payload: CreateProposalRequest, context: DatasetContext) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(payload, context)},
    ]


def build_user_prompt(payload: CreateProposalRequest, context: DatasetContext) -> str:
    capabilities = infer_dataset_capabilities(context)
    analysis_plan = plan_analysis_request(normalize_text(payload.user_request), capabilities)
    prompt_payload = {
        "phien_ban_prompt": PROMPT_VERSION,
        "nhiem_vu": "Tạo proposal AI cho quy trình phân tích dữ liệu có con người xem xét và phê duyệt trước khi chạy.",
        "che_do": payload.mode,
        "yeu_cau_nguoi_dung": payload.user_request,
        "ngu_canh_du_lieu": serialize_dataset_context(context),
        "nang_luc_dataset": serialize_capabilities(capabilities),
        "ke_hoach_phan_tich_backend": {
            "intent": analysis_plan.intent_names,
            "co_the_thuc_thi": analysis_plan.can_execute,
            "ly_do_thieu_schema": analysis_plan.missing_reasons,
            "chien_luoc_goi_y": analysis_plan.recommended_strategy,
        },
        "goi_y_phan_tich_kha_thi": analysis_suggestions(context),
        "thu_vien_duoc_phep": ALLOWED_LIBRARIES,
        "vi_du_dieu_huong": FEW_SHOT_EXAMPLES,
        "hop_dong_runtime": {
            "ten_dataframe_dau_vao": "df",
            "bien_thu_muc_output": "outputs_dir",
            "bat_buoc_copy_truoc_khi_bien_doi": "work_df = df.copy()",
            "quy_tac_thuc_thi": "Backend sẽ hiển thị code cho người dùng xem trước. Code chỉ được chạy sau khi người dùng phê duyệt.",
            "quy_tac_nhan_xet_sau_chay": "Không viết nhận xét giả trong code. Sau execution, AI insight sẽ dùng stdout, bảng artifact và metadata artifact thật để nhận xét.",
        },
        "rang_buoc_do_dai": {
            "so_dong_code_toi_da_goi_y": MAX_CODE_LINES_HINT,
            "stdout": "In bảng/thống kê thật ngắn gọn. Không in toàn bộ dataset nếu bảng có nhiều dòng; dùng head/top hoặc summary.",
        },
        "schema_phan_hoi_bat_buoc": compact_response_contract(),
        "luu_y_ve_schema": "Các tên field trong schema phản hồi như summary, code, explanation, assumptions, risk_flags, expected_outputs phải giữ nguyên để backend validate được JSON.",
    }
    return json.dumps(prompt_payload, ensure_ascii=False, separators=(",", ":"), default=str)


def serialize_dataset_context(context: DatasetContext) -> dict[str, Any]:
    return {
        "ma_dataset": context.id,
        "ten_dataset": context.name,
        "so_dong": context.rows,
        "trang_thai": context.status,
        "cac_cot": [
            {
                "ten_cot": column.name,
                "kieu_du_lieu": column.dtype,
                "so_gia_tri_null": column.nullable_count,
                "gia_tri_mau": column.sample_values,
                "so_gia_tri_duy_nhat": column.unique_count,
                "top_gia_tri": column.top_values,
                "tom_tat_so": column.numeric_summary,
            }
            for column in context.columns
        ],
    }


def render_schema_for_docs() -> str:
    return json.dumps(PROPOSAL_JSON_SCHEMA, ensure_ascii=True, indent=2)


def compact_response_contract() -> dict[str, Any]:
    required = PROPOSAL_JSON_SCHEMA["required"]
    return {
        "required": required,
        "required_fields": required,
        "risk_flags_enum": PROPOSAL_JSON_SCHEMA["properties"]["risk_flags"]["items"]["enum"],
        "expected_outputs_enum": PROPOSAL_JSON_SCHEMA["properties"]["expected_outputs"]["items"]["enum"],
        "response_must_be_json_object": True,
    }
