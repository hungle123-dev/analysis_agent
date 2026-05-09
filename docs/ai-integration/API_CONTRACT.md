# API Contract

## Nguyen tac

API nen tach 4 nhom:

1. Dataset API: cho biet du lieu nao duoc phep phan tich.
2. AI Proposal API: tao code/giai thich, khong chay.
3. Approval + Execution API: nguoi dung duyet roi moi chay local.
4. Logs API: truy xuat toan bo qua trinh.

## Dataset API

### `GET /api/datasets`

Tra danh sach dataset da dang ky.

### `GET /api/datasets/{dataset_id}/context`

Tra context an toan cho AI:

```json
{
  "dataset_id": "sales",
  "name": "sales.csv",
  "row_count": 1200,
  "columns": [
    {
      "name": "date",
      "dtype": "datetime",
      "nullable_count": 0,
      "sample_values": ["2025-01-01", "2025-01-02"]
    },
    {
      "name": "revenue",
      "dtype": "float",
      "nullable_count": 15,
      "sample_values": [1200000, 980000]
    }
  ]
}
```

## AI Proposal API

### `POST /api/ai/proposals`

Tao proposal tu AI. Khong thuc thi code.

Request:

```json
{
  "session_id": "demo_01",
  "dataset_id": "sales",
  "user_request": "Ve bieu do doanh thu theo thang va nhan xet xu huong",
  "mode": "generate_code"
}
```

Response:

```json
{
  "proposal_id": "prop_001",
  "status": "pending_review",
  "summary": "Tinh tong revenue theo thang va ve line chart.",
  "code": "# Doan code nay tao ban sao dataframe de khong thay doi du lieu goc.\nwork_df = df.copy()\n...",
  "explanation": "Code tao cot month, group by theo month, tinh tong revenue va luu bieu do vao outputs.",
  "assumptions": ["Cot date la ngay giao dich", "Cot revenue la doanh thu"],
  "risk_flags": ["creates_chart_file"],
  "expected_outputs": ["table", "chart"]
}
```

### `POST /api/ai/proposals/jobs`

Tao background job de AI sinh proposal ma khong khoa request frontend trong luc doi model.

Request giong `POST /api/ai/proposals`.

Response:

```json
{
  "job_id": "job_001",
  "status": "queued",
  "dataset_id": "sales",
  "trace_id": null,
  "proposal_id": null,
  "error": null,
  "created_at": "2026-05-09T02:00:00+00:00",
  "updated_at": "2026-05-09T02:00:00+00:00"
}
```

### `GET /api/ai/proposals/jobs/{job_id}`

Frontend poll endpoint nay moi 1-2 giay. Khi `status = "succeeded"`, response co `proposal_id`.

### `GET /api/ai/proposals/{proposal_id}`

Lay proposal sau khi background job hoan tat.

## Edit/Approval API

### `PATCH /api/ai/proposals/{proposal_id}`

Luu code nguoi dung da sua.

```json
{
  "edited_by": "student_01",
  "edited_code": "# Code sau khi nguoi dung sua..."
}
```

### `POST /api/ai/proposals/{proposal_id}/approve`

Phe duyet ban code hien tai.

```json
{
  "approved_by": "student_01",
  "approval_note": "Da kiem tra code va doi mau bieu do."
}
```

Response:

```json
{
  "proposal_id": "prop_001",
  "status": "approved",
  "code_hash": "sha256:abc..."
}
```

### `POST /api/ai/proposals/{proposal_id}/reject`

Tu choi proposal truoc khi chay local. Backend phai luu audit event de chung minh con nguoi da quyet dinh khong thuc thi code nay.

```json
{
  "rejected_by": "student_01",
  "rejection_reason": "Can doi cach ve bieu do"
}
```

Response tra lai proposal voi `status = "rejected"` va `code_hash = null`.

## Execution API

### `POST /api/executions`

Chay code da duyet tren local.

```json
{
  "proposal_id": "prop_001",
  "dataset_id": "sales",
  "code_hash": "sha256:abc...",
  "requested_by": "student_01"
}
```

Response:

```json
{
  "run_id": "run_001",
  "status": "succeeded",
  "stdout": "Saved chart to outputs/run_001/revenue_by_month.png",
  "stderr": "",
  "return_code": 0,
  "duration_ms": 1420,
  "started_at": "2026-05-08T14:05:10.100000+00:00",
  "finished_at": "2026-05-08T14:05:11.520000+00:00",
  "artifacts": [
    {
      "type": "chart",
      "name": "revenue_by_month",
      "path": "outputs/run_001/revenue_by_month.png"
    }
  ]
}
```

`artifacts[].type` chuan hoa:

- `chart`: `.png`, `.jpg`, `.jpeg`, `.svg`, `.webp`
- `table`: `.csv`, `.json`, `.parquet`, `.xlsx`
- `log`: `.txt`, `.log`
- `text`: cac file text khac

Backend phai reject neu:

- proposal chua approved
- proposal dang running, da succeeded, failed, hoac rejected
- code_hash khong khop
- code vi pham policy
- dataset_id khong duoc dang ky

Khi code vi pham policy, backend tra chi tiet:

```json
{
  "detail": {
    "policy_errors": [
      {
        "code": "blocked_import",
        "message": "Import khong duoc phep: os",
        "severity": "error"
      }
    ]
  }
}
```

## Logs API

### `GET /api/logs`

Filter:

- `session_id`
- `proposal_id`
- `run_id`
- `event_type`
- `status`

### `GET /api/logs/{trace_id}`

Tra toan bo chuoi:

```json
{
  "trace_id": "trace_001",
  "events": [
    "ai.request.created",
    "ai.proposal.generated",
    "ai.proposal.edited",
    "ai.approval.approved",
    "ai.approval.rejected",
    "execution.started",
    "execution.succeeded"
  ]
}
```
