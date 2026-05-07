# PHANCONG.md

## Muc tieu chung

Hoan thien AI Analysis Workbench theo flow:

```text
user request -> AI proposal -> user review/edit -> approval -> local execution -> logs/results
```

AI khong duoc chay ngam. Backend phai enforce approval va policy, frontend phai hien ro code/result/log cho nguoi dung.

## Pham vi da giao cho ban: Prompt Engineering

Trang thai hien tai:

- Da tao `backend/app/services/prompt_builder.py`.
- Da dinh nghia system prompt, user prompt payload, allowed libraries, runtime contract va response JSON schema.
- Da cap nhat `docs/ai-integration/AI_PROMPTS_AND_SCHEMA.md`.
- Da them test `backend/tests/test_prompt_builder.py`.

Phan nay tiep tuc do ban phu trach:

- Tinh chinh prompt khi tich hop provider that.
- Them prompt rieng cho `suggestions` va `explain_result` neu can.
- Kiem tra AI co tra dung JSON schema khong.
- Cap nhat tai lieu prompt khi rule thay doi.

## Thanh vien 1: Backend Core, Safety, Dataset

### Muc tieu

Lam backend chac, an toan, khong hardcode dataset va enforce dung yeu cau cua thay.

### File chinh

```text
backend/app/services/dataset_service.py
backend/app/services/policy_checker.py
backend/app/services/execution_runner.py
backend/app/schemas.py
backend/tests/
backend/config/datasets.json
```

### Task 1: DatasetRegistry

Can lam:

- Tao `backend/config/datasets.json`.
- Moi dataset co:
  - `id`
  - `name`
  - `path`
  - `description`
  - `allowed`
  - `created_by`
- Refactor `dataset_service.py` de doc config thay vi hardcode `DATASETS`.
- Backend chi cho doc dataset co trong registry va `allowed=true`.
- API dataset context can tra:
  - dataset id/name/status
  - so dong
  - column schema
  - null count
  - sample values

Tieu chi hoan thanh:

- `GET /api/datasets` khong phu thuoc hardcode trong code.
- Dataset khong co trong registry bi reject.
- Test dataset hop le/khong hop le pass.

### Task 2: PolicyChecker nang cap

Can lam:

- Doi policy result tu `list[str]` sang object ro rang:
  - `code`
  - `message`
  - `severity`
- Chia nhom loi:
  - `blocked_import`
  - `blocked_call`
  - `dataset_mutation`
  - `unsafe_output_path`
  - `unsafe_data_read`
- Giu cac rule hien co:
  - chan import nguy hiem
  - chan shell/network/file access
  - chan sua truc tiep `df`
  - chi cho ghi output vao `outputs_dir`
- Them unit test rieng cho tung rule.

Tieu chi hoan thanh:

- Frontend co the hien thi policy error theo severity.
- Code nguy hiem bi reject o ca edit/approve/execute.
- Code hop le cua mock provider van approve va execute duoc.

### Task 3: ExecutionRunner nang cap

Can lam:

- Capture them:
  - `return_code`
  - `duration_ms`
  - `started_at`
  - `finished_at`
- Timeout doc tu config/env, vi du `EXECUTION_TIMEOUT_SECONDS=30`.
- Luu runner metadata vao DB/log.
- Dam bao code chi chay trong `runs/{run_id}` va chi ghi vao `outputs`.
- Chuan hoa artifact type:
  - `chart`
  - `table`
  - `text`
  - `log`

Tieu chi hoan thanh:

- Run thanh cong co stdout/artifact/duration.
- Run loi co stderr va status `failed`.
- Run timeout co error ro rang va duoc log.

## Thanh vien 2: Frontend Integration, Result UI, Logs UI

### Muc tieu

Lam frontend dung nhu workbench: user thay code, sua code, approve, run local, xem result/policy/log that tu backend.

### File chinh

```text
frontend/src/App.jsx
frontend/src/api/client.js
frontend/src/components/workbench/ProposalEditor.jsx
frontend/src/components/workbench/ApprovalGate.jsx
frontend/src/components/workbench/Inspector/ResultTab.jsx
frontend/src/components/workbench/Inspector/PolicyTab.jsx
frontend/src/components/workbench/Inspector/LogsTab.jsx
```

### Task 1: Result Viewer that

Can lam:

- Bo mock rows trong result tab.
- Hien chart artifact that tu backend.
- Hien stdout/stderr ro rang.
- Neu backend tra table artifact CSV/JSON thi render thanh table.
- Neu execution failed thi hien error state dung muc.

Tieu chi hoan thanh:

- Sau khi run thanh cong, user thay chart va stdout that.
- Khong con du lieu fake trong UI result.

### Task 2: Policy Tab that

Can lam:

- Lay policy result/error that tu backend.
- Hien thi:
  - severity
  - error code
  - message
- Khi code bi reject luc edit/approve, tu dong chuyen sang tab Policy.
- Khong cho user run neu policy dang fail.

Tieu chi hoan thanh:

- Paste code `import os; os.system(...)` thi UI hien ly do bi chan.
- Code hop le thi policy tab hien trang thai pass.

### Task 3: Logs Timeline that

Can lam:

- Goi `GET /api/logs/{trace_id}` sau moi proposal/approve/run.
- Hien timeline:
  - `ai.request.created`
  - `ai.proposal.generated`
  - `ai.proposal.edited`
  - `ai.approval.approved`
  - `execution.started`
  - `execution.succeeded` hoac `execution.failed`
- Hien actor, timestamp, payload tom tat.

Tieu chi hoan thanh:

- Demo co the mo Logs va truy lai toan bo workflow.
- Log khong bi fake trong frontend.

### Task 4: Approval UX

Can lam:

- Neu user sua code sau approve, trang thai ve `edited` va bat approve lai.
- Nut Run chi enable khi:
  - proposal status la `approved`
  - co `code_hash`
  - code hien tai khop code da approve
- Hien status ro:
  - `pending_review`
  - `edited`
  - `approved`
  - `running`
  - `succeeded`
  - `failed`

Tieu chi hoan thanh:

- Khong the bam Run khi chua approve.
- Sua code sau approve khong the run bang hash cu.

## Quy tac phoi hop

- Ban phu trach prompt chi sua:
  - `backend/app/services/prompt_builder.py`
  - provider prompt integration neu can
  - `docs/ai-integration/AI_PROMPTS_AND_SCHEMA.md`
- Thanh vien 1 uu tien backend services/tests.
- Thanh vien 2 uu tien frontend components/client.
- `backend/app/schemas.py` la file giao nhau. Ai can sua phai bao truoc.
- Khong sua hoac revert file cua nguoi khac khi chua thong nhat.
- Moi task backend phai co test.
- Moi task frontend quan trong nen co screenshot/manual smoke test.

## Thu tu lam de it conflict

1. Thanh vien 1 lam DatasetRegistry va PolicyChecker object.
2. Ban cap nhat prompt neu schema policy/proposal thay doi.
3. Thanh vien 2 noi frontend theo API/result/policy/log moi.
4. Ca nhom chay demo end-to-end.
5. Sau cung moi polish docs va bao cao.
