# AI Prompts And Schema

## Muc tieu

Prompt engineering cua module AI phai phuc vu dung yeu cau cua thay: AI chi de xuat/viet code/giai thich, con nguoi moi la nguoi phe duyet va code chi chay local sau khi duoc approve.

## Cau hinh provider nhanh cho ds2api

Khi dung ds2api, nen uu tien model khong thinking cho thao tac tao proposal/code ngan:

```env
AI_PROVIDER=deepseek
DEEPSEEK_BASE_URL=http://127.0.0.1:5001
DEEPSEEK_MODEL=deepseek-v4-flash-nothinking
DEEPSEEK_INSIGHT_MODEL=deepseek-v4-flash-nothinking
DEEPSEEK_MAX_TOKENS=2200
DEEPSEEK_INSIGHT_MAX_TOKENS=900
DEEPSEEK_TEMPERATURE=0.2
DEEPSEEK_TIMEOUT_SECONDS=60
DEEPSEEK_THINKING=disabled
AI_EXPLAIN_RESULT_ENABLED=true
AI_EXPLAIN_RESULT_PROVIDER=deepseek
AI_EXPLAIN_RESULT_TIMEOUT_SECONDS=45
EXECUTION_TIMEOUT_SECONDS=60
```

Ly do: ung dung can code de nguoi dung review, khong can model sinh reasoning dai. Sau moi lan generate, xem `ai.proposal.generated` trong Logs de kiem tra `llm_duration_ms`, token usage va cache hit/miss.
Sau moi lan execution thanh cong, ds2api/DeepSeek nhan xet dua tren stdout, table preview va artifact metadata that. Bieu do chi la minh hoa truc quan, khong phai nguon so lieu chinh cho AI. Prompt insight la evidence-only: khong gui code dai vao buoc nhan xet va cam model nhac nhom/dia danh/cot neu chuoi do khong xuat hien trong evidence.

## UX latency

Frontend nen goi `POST /api/ai/proposals/jobs` thay vi cho request sync doi den khi model tra xong. Flow polling:

```text
Generate -> job_id -> poll status -> proposal_id -> hien code cho nguoi dung review
```

Flow nay khong lam model chay nhanh hon, nhung tranh cam giac UI bi dung trong 20+ giay khi dung ds2api.

Prompt khong duoc de AI tra ve markdown lan man. Provider that nhu DeepSeek/OpenAI-compatible/Ollama can tra JSON dung schema de backend validate truoc khi hien thi cho frontend.

Implementation source:

```text
backend/app/services/prompt_builder.py
backend/app/services/analysis_intent.py
backend/app/services/dataset_capabilities.py
```

Truoc khi goi LLM, backend dung `AnalysisIntentPlanner` de phan loai prompt thanh cac intent tong quat: distribution, correlation, group comparison, time series, revenue/profit, funnel/conversion, retention va coordinate map. Planner doi chieu intent voi capability that cua dataset. Neu thieu cot bat buoc, backend tra proposal text-only va khong cho AI tu ve chart thay the. Neu du capability, user prompt payload van gui `ke_hoach_phan_tich_backend` cho LLM de giam nguy co sinh code lech schema.

## Nguyen tac prompt bat buoc

- AI khong duoc thuc thi code.
- AI khong duoc bia so lieu, cot, bieu do, hinh anh hoac ket qua.
- AI chi duoc dung dataset context do backend gui vao.
- Neu chua co execution artifact, AI khong duoc ket luan bang so lieu.
- Code Python phai gia dinh dataframe dau vao ten la `df`.
- Truoc khi bien doi du lieu, code phai dung `work_df = df.copy()`.
- Code khong duoc sua `df` goc.
- Code chi duoc ghi artifact vao `outputs_dir`.
- Code khong duoc doc file khac, goi shell, goi network, import module nguy hiem.
- Code phai co comment tieng Viet giai thich thao tac quan trong.
- Response phai la JSON thuan, khong boc markdown.

## System Prompt

System prompt duoc dinh nghia trong `SYSTEM_PROMPT`:

```text
Ban la AI ho tro phan tich du lieu trong mot ung dung local.

Vai tro cua ban:
- De xuat huong phan tich khi nguoi dung chua ro nen lam gi.
- Tao code Python phan tich du lieu theo yeu cau cua nguoi dung.
- Giai thich code va ket qua dua tren du lieu/artifact he thong cung cap.

Quy tac bat buoc:
- Khong duoc thuc thi code.
- Khong duoc tu y them so lieu, ten cot, hinh anh, bieu do hoac ket qua khong co trong context.
- Khong duoc ket luan bang so lieu neu chua co ket qua thuc thi/artifact.
- Code Python phai gia dinh dataframe dau vao ten la df.
- Chi duoc dung ten cot xuat hien trong dataset context. Khong duoc gia dinh cac cot nhu `date`, `month`, `ngay_dang`, `revenue` neu schema khong co.
- Neu yeu cau can cot khong ton tai, AI phai tao proposal text-only de giai thich ly do va goi y huong phan tich thay the bang cot co that.
- Neu code co nhanh validation phat hien khong the tao artifact da hua, code phai `raise ValueError` de backend danh dau failed, khong duoc chi `print()` loi roi ket thuc return code 0.
- Truoc khi bien doi du lieu, code phai tao ban sao: work_df = df.copy().
- Khong duoc sua df goc, khong duoc ghi de dataset goc.
- Chi duoc ghi output vao outputs_dir do backend cung cap.
- Khong duoc doc file khac, goi shell, goi network, import module nguy hiem.
- Moi khoi code quan trong phai co comment tieng Viet giai thich thao tac.
- Tra ve duy nhat JSON dung schema, khong boc markdown, khong them van ban ben ngoai JSON.
```

## User Prompt Payload

Backend gui user prompt duoi dang JSON:

```json
{
  "task": "Create an AI proposal for a human-in-the-loop data analysis workflow.",
  "mode": "generate_code",
  "user_request": "Ve doanh thu theo thang",
  "dataset_context": {
    "dataset_id": "sales_2025",
    "name": "sales_2025.csv",
    "row_count": 4,
    "status": "ready",
    "columns": [
      {
        "name": "date",
        "dtype": "object",
        "nullable_count": 0,
        "sample_values": ["2025-01-05"]
      },
      {
        "name": "revenue",
        "dtype": "int64",
        "nullable_count": 0,
        "sample_values": [1240000]
      }
    ]
  },
  "allowed_libraries": [
    "pandas",
    "numpy",
    "matplotlib",
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
    "statistics"
  ],
  "runtime_contract": {
    "input_dataframe_name": "df",
    "output_directory_variable": "outputs_dir",
    "must_copy_dataframe_before_mutation": "work_df = df.copy()",
    "execution": "The backend will show code to the user first. Execution happens only after approval."
  },
  "response_schema": {
    "type": "object"
  }
}
```

## Proposal Schema

Response bat buoc co cac field:

```json
{
  "summary": "string",
  "code": "string",
  "explanation": "string",
  "assumptions": ["string"],
  "risk_flags": ["creates_chart_file"],
  "expected_outputs": ["table", "chart", "log"]
}
```

`risk_flags` hop le:

- `changes_dtype`
- `creates_chart_file`
- `creates_table_file`
- `creates_table_stdout`
- `drops_rows`
- `filters_outliers`
- `needs_human_check`
- `uses_statistical_model`

`expected_outputs` hop le:

- `text`
- `table`
- `chart`
- `log`

## Vi Du Response Tot

```json
{
  "summary": "Tinh tong doanh thu theo thang va ve line chart.",
  "code": "# Doan code nay tao ban sao dataframe de khong thay doi du lieu goc.\nwork_df = df.copy()\n\n# Doan code nay chuyen cot date sang kieu ngay thang de co the nhom theo thang.\nwork_df[\"date\"] = pd.to_datetime(work_df[\"date\"])\n\n# Doan code nay tao cot month va tinh tong revenue theo tung thang.\nwork_df[\"month\"] = work_df[\"date\"].dt.to_period(\"M\").astype(str)\nmonthly = work_df.groupby(\"month\", as_index=False)[\"revenue\"].sum()\n\n# Doan code nay ve bieu do va luu vao outputs_dir cua lan chay.\nplt.figure(figsize=(10, 5))\nplt.plot(monthly[\"month\"], monthly[\"revenue\"], marker=\"o\")\nplt.xticks(rotation=45)\nplt.tight_layout()\nplt.savefig(outputs_dir / \"revenue_by_month.png\")\n\n# Doan code nay in bang tong hop de frontend hien thi.\nprint(monthly.to_string(index=False))",
  "explanation": "Code tao ban sao df, chuyen date sang datetime, nhom revenue theo thang, in bang tong hop va luu line chart vao outputs_dir.",
  "assumptions": ["Cot date la ngay giao dich", "Cot revenue la doanh thu"],
  "risk_flags": ["changes_dtype", "creates_chart_file", "creates_table_stdout"],
  "expected_outputs": ["table", "chart", "log"]
}
```

## Prompt Cho Che Do Goi Y Phan Tich

Dung khi nguoi dung chua biet nen hoi gi:

```text
Dua tren dataset_context, hay de xuat cac cau hoi phan tich co the tra loi bang cac cot hien co.
Moi goi y can neu: muc dich, cot can dung, bieu do phu hop, va ly do huu ich.
Khong tao so lieu gia dinh. Khong nhac cot khong co trong dataset_context.
```

## Prompt Cho Che Do Giai Thich Ket Qua

Chi dung sau khi code da chay va co artifact:

```text
Hay giai thich ket qua dua tren artifact summary duoc cung cap.
Chi duoc nhac so lieu co trong artifact.
Neu can them thong tin, hay noi ro can chay phan tich nao tiep theo.
```

## Tieu Chi Review Prompt

- Response parse duoc bang JSON parser.
- Field `code` co comment tieng Viet.
- Code bat dau bang hoac co `work_df = df.copy()` truoc bien doi.
- Code khong dung cot nam ngoai dataset context.
- Code khong doc/ghi file tuy tien.
- Code chi luu output qua `outputs_dir`.
- Neu prompt la explain result, AI chi giai thich tu artifact da co.
