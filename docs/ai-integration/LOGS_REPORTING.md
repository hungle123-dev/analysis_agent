# Logs And Reporting

## Vi sao logs la phan bat buoc

Thay yeu cau he thong luu tat ca yeu cau, ma nguon, ket qua phan tich va giai thich. Vi vay logs khong phai phu kien; no la bang chung de bao ve rang nhom da dung AI dung quy trinh.

## Trace can luu

Moi cau hoi nen co `trace_id`:

```text
request -> proposal -> edit -> approval -> execution -> result -> explanation
```

## Event types

- `ai.request.created`
- `ai.proposal.generated`
- `ai.proposal.validation_failed`
- `ai.proposal.edited`
- `ai.approval.approved`
- `ai.approval.rejected`
- `execution.started`
- `execution.succeeded`
- `execution.failed`
- `ai.result.explained`

## Bang SQLite toi thieu

### `ai_requests`

- `request_id`
- `trace_id`
- `session_id`
- `dataset_id`
- `user_prompt`
- `created_by`
- `created_at`

### `ai_proposals`

- `proposal_id`
- `trace_id`
- `summary`
- `ai_code`
- `edited_code`
- `explanation`
- `assumptions_json`
- `risk_flags_json`
- `status`
- `created_at`

### `approvals`

- `approval_id`
- `proposal_id`
- `approved_by`
- `approved_at`
- `approval_note`
- `code_hash`

### `executions`

- `run_id`
- `proposal_id`
- `status`
- `stdout`
- `stderr`
- `artifacts_json`
- `started_at`
- `finished_at`
- `duration_ms`

### `audit_events`

- `event_id`
- `trace_id`
- `event_type`
- `actor`
- `timestamp`
- `payload_json`

## Artifact rules

- Chart luu vao `outputs/{run_id}/`.
- Bang ket qua luu CSV/JSON vao `outputs/{run_id}/`.
- Khong luu de file dataset goc.
- Neu dataset co du lieu nhay cam, log schema/hash thay vi dump toan bo data.

## Noi dung dua vao bao cao

### Qua trinh su dung AI

Mo ta ngan:

1. Nguoi dung nhap yeu cau.
2. AI tao code/giai thich.
3. Nguoi dung xem va sua code.
4. Nguoi dung approve.
5. He thong chay local va luu ket qua.
6. Log cho phep truy xuat lai.

### Bang tong hop yeu cau

| STT | Yeu cau | AI tra ve | Nhom sua gi | Ket qua | Log/Run |
| --- | --- | --- | --- | --- | --- |
| 1 | Ve doanh thu theo thang | Code groupby + chart | Doi mau chart | Thanh cong | run_001 |

### Nhan xet ve AI

- AI giup tao code nhanh va goi y huong phan tich.
- AI co the nham ten cot nen can schema validation va nguoi dung review.
- AI khong duoc tu ket luan neu chua co artifact.
- Workflow approval giup dam bao con nguoi van quyet dinh.

## Man hinh nen chup lam minh chung

- Request cua nguoi dung.
- Code AI sinh o trang thai pending_review.
- Man hinh sua code.
- Man hinh approve.
- Ket qua execution.
- Log chi tiet cua trace_id.
