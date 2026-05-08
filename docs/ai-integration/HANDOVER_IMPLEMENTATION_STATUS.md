# HANDOVER IMPLEMENTATION STATUS

## 1) Mục tiêu project (đối chiếu)

Project được xây dựng theo luồng:

```text
user request -> AI proposal -> user review/edit -> approval -> local execution -> logs/results
```

Nguồn đối chiếu:

- `AGENTS.md`
- `PHANCONG.md`
- `docs/ai-integration/SOFTWARE_DESIGN_PRINCIPLES.md`
- `docs/ai-integration/API_CONTRACT.md`
- `docs/ai-integration/AI_PROMPTS_AND_SCHEMA.md`
- `docs/ai-integration/HUMAN_APPROVAL_EXECUTION.md`
- `docs/ai-integration/LOGS_REPORTING.md`
- `docs/ai-integration/REQUIREMENT_TRACEABILITY.md`

---

## 2) Tổng kết những gì đã hoàn thành

### 2.1 Backend workflow core

- Đã có đầy đủ API chính:
  - `GET /api/datasets`
  - `GET /api/datasets/{dataset_id}/context`
  - `POST /api/ai/proposals`
  - `PATCH /api/ai/proposals/{proposal_id}`
  - `POST /api/ai/proposals/{proposal_id}/approve`
  - `POST /api/executions`
  - `GET /api/logs/{trace_id}`
- Đã enforce luồng human approval:
  - Chưa approve thì không cho execute.
  - `code_hash` mismatch thì reject execute.
- Đã có local execution runner:
  - Chạy code trong `runs/{run_id}`.
  - Tạo artifact trong `runs/{run_id}/outputs`.
  - Capture `stdout/stderr`.

### 2.2 Dataset và dữ liệu thật

- Đã thêm `cleaned_vietnam_real_estate.csv`.
- Đã có `data_processing.py` để xử lý dữ liệu.
- Đã refactor theo hướng DatasetRegistry config file:
  - `backend/config/datasets.json`
  - `backend/app/services/dataset_service.py` đọc registry thay vì hardcode thuần.
- Đã expose dataset context (schema, null count, sample values) cho AI.

### 2.3 AI provider và prompt

- Đã tích hợp provider DeepSeek:
  - `backend/app/services/deepseek_llm_provider.py`
  - `backend/app/services/llm_provider.py` hỗ trợ `AI_PROVIDER=deepseek|mock`.
- Đã dùng prompt contract từ `prompt_builder.py`, parse JSON response schema.
- Đã bổ sung env sample:
  - `.env.example` (không chứa key thật).

### 2.4 Policy checker + UI policy

- Policy checker đang hoạt động ở 3 gate:
  - edit proposal
  - approve proposal
  - execute
- Đã chuyển policy errors sang object có cấu trúc:
  - `code`
  - `message`
  - `severity`
- Frontend Policy tab đã hiển thị lỗi thật từ backend (không còn checklist tĩnh là chính).

### 2.5 Execution metadata + artifacts

- Đã bổ sung metadata execution:
  - `return_code`
  - `duration_ms`
  - `started_at`
  - `finished_at`
- Đã lưu artifact chart và hiển thị trên tab Output.

### 2.6 Logging/Audit

- Đã lưu audit events theo `trace_id`.
- Đã có timeline logs trong UI qua `/api/logs/{trace_id}`.
- Đã có các event chính:
  - request/proposal/edit/approve/execution start/success/fail.

### 2.7 Test và run

- Backend tests đang pass:
  - `backend/tests/test_dataset_service.py`
  - `backend/tests/test_prompt_builder.py`
  - `backend/tests/test_workflow.py`
- Frontend build pass.

---

## 3) Cách run hiện tại (handover quick start)

## 3.1 Backend

```bash
cd /Users/toannguyen/analysis_agent
source .venv/bin/activate
set -a
source .env
set +a
./.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Lưu ý:

- Không gộp các lệnh `source/set/uvicorn` thành 1 dòng liền nhau.
- Cần restart backend sau khi đổi `.env`.

## 3.2 Frontend

```bash
cd /Users/toannguyen/analysis_agent
npm run dev --prefix frontend
```

## 3.3 Vị trí artifact sau khi run local

- `runs/<run_id>/outputs/*`
- Chart được mount qua static route `/artifacts/...` để frontend hiển thị.

---

## 4) Tình trạng hiện tại theo yêu cầu project

### Đã đạt (MVP demo level)

- Human-in-the-loop workflow đã chạy được.
- AI code được hiển thị trước, user có thể sửa, approve rồi mới run.
- Backend enforce state transition (không chỉ frontend check).
- Local execution + logs + artifact đã có.
- Đã tích hợp được provider AI thật (DeepSeek), có fallback qua mock khi cần.

### Chưa đạt hoàn toàn (cần làm tiếp để "chốt đồ án")

- Chưa có artifact table/text parser đầy đủ (hiện mới chart/stdout là chính).
- Prompt để phát sinh code an toàn hơn với seaborn/matplotlib chưa tối ưu (vẫn có warning).
- Chưa có bộ test riêng cho DeepSeek provider và fallback paths.
- Chưa cập nhật đầy đủ docs contract theo implementation mới (policy object, execution metadata, fallback event).
- Chưa có e2e frontend tests.

---

## 5) Backlog cần làm tiếp (ưu tiên rõ ràng)

## P0 - Cần làm ngay để bàn giao an toàn

1. Cập nhật docs cho khớp code hiện tại:
   - `docs/ai-integration/API_CONTRACT.md`
   - `docs/ai-integration/AI_PROMPTS_AND_SCHEMA.md`
   - `docs/ai-integration/LOGS_REPORTING.md`
2. Chỉnh Prompt/Provider để giảm code vi phạm policy:
   - tránh `import os`
   - bắt buộc `plt.savefig(outputs_dir / "...")`
3. Cải tiến Output tab:
   - Khi `execution failed`, ưu tiên hiển thị `stderr` rõ ràng (không chỉ "No local artifacts").

## P1 - Để hoàn thiện tính năng

1. Artifact normalization:
   - map `chart/table/text/log` rõ ràng từ outputs.
   - render table artifact trên frontend.
2. DeepSeek robustness:
   - retry/backoff có giới hạn
   - logs event rõ cho fallback.
3. Policy UX:
   - Hiển thị issue severity + code + message dễ đọc hơn nữa.

## P2 - Chất lượng và báo cáo

1. Bổ sung test:
   - provider integration contract tests (mock API response)
   - execution fail/timeout tests chi tiết hơn
2. Demo assets:
   - screenshot cho mỗi stage workflow
   - trace log minh chứng theo `DEMO_QA.md`
3. Requirement traceability:
   - đối chiếu `REQUIREMENT_TRACEABILITY.md` với implementation đã có.

---

## 6) Đề xuất chia task tiếp theo (ít conflict)

Phần Backend Core/Safety đã được làm nền tương đối đầy đủ. Đề xuất tập trung cho 2 người còn lại như sau:

### Người 1 - Prompt/AI Integration (chỉnh AI phù hợp dataset thật)

Mục tiêu:

- Giảm lỗi code vi phạm policy.
- Tăng chất lượng code sinh ra cho dataset `cleaned_vietnam_real_estate.csv`.
- Giảm warning seaborn/matplotlib trong code AI generate.

File chính:

- `backend/app/services/prompt_builder.py`
- `backend/app/services/deepseek_llm_provider.py`
- `docs/ai-integration/AI_PROMPTS_AND_SCHEMA.md`

Việc cụ thể:

- Cập nhật prompt để ép AI:
  - không `import os`
  - chỉ lưu file qua `outputs_dir / "..."` (không dùng chuỗi path tự do)
  - ưu tiên chart phù hợp với các cột thực tế (`Tinh_Thanh`, `Gia_Trieu_VND`, `Dien_Tich_m2`, ...)
- Thêm guideline xử lý dữ liệu:
  - kiểm tra null/empty trước khi vẽ
  - tránh crash khi lọc dữ liệu rỗng
- Tinh chỉnh output schema:
  - `risk_flags` và `expected_outputs` nhất quán hơn với code thực tế
- Cập nhật tài liệu prompt để người khác dùng lại đúng chuẩn.

Tiêu chí hoàn thành:

- Tạo proposal 5 lần liên tiếp, tối thiểu 4 lần pass policy ngay từ lần generate đầu.
- Không còn lỗi phổ biến `blocked_import` và `unsafe_output_path`.

### Người 2 - Frontend Integration/UI Polish (chỉnh UI cho dễ dùng và đẹp hơn)

Mục tiêu:

- Làm UI rõ trạng thái, dễ debug, dễ demo.
- Hiển thị kết quả/ lỗi thực tế thay vì trạng thái chung chung.

File chính:

- `frontend/src/App.jsx`
- `frontend/src/api/client.js`
- `frontend/src/components/workbench/Inspector/ResultTab.jsx`
- `frontend/src/components/workbench/Inspector/PolicyTab.jsx`
- `frontend/src/components/workbench/Inspector/LogsTab.jsx`
- (tuỳ chọn) `frontend/src/styles.css`

Việc cụ thể:

- Cải thiện tab Output:
  - khi fail thì hiện `stderr` nổi bật, không chỉ "No local artifacts"
  - hiển thị rõ `run_id`, `duration_ms`, `return_code`
- Cải thiện tab Policy:
  - hiển thị tốt `code/message/severity`
  - làm visual rõ mức độ lỗi
- Cải thiện tab Logs:
  - format payload dễ đọc hơn (event quan trọng hiển thị rõ)
- Polish giao diện:
  - spacing/màu/chữ dễ đọc hơn để demo
  - giữ phong cách workbench nhưng giảm rối

Tiêu chí hoàn thành:

- Demo 3 case mượt:
  - success run có chart + metadata
  - policy fail thấy rõ lỗi và lý do
  - execution fail thấy rõ `stderr` để xử lý nhanh

Quy tắc:

- Nếu sửa `backend/app/schemas.py` thì thông báo team trước.
- Merge theo thứ tự: backend contract -> prompt -> frontend.

---

## 7) Rủi ro đã biết và cách xử lý

- DeepSeek có thể bị `429`/quota:
  - Đang có fallback mock; cần thông báo rõ trên UI/logs.
- AI code có thể vi phạm policy:
  - Workflow yêu cầu user review/edit trước approve.
- Warning seaborn (FutureWarning):
  - Không làm fail run, nhưng nên fix syntax để warning-free.

---

## 8) Trạng thái handover

Project hiện tại đã ở mức:

```text
Có thể demo full workflow với dataset thật, AI đề xuất code, user approve, run local, và xem artifact/log.
```

Cần tiếp tục theo backlog P0 -> P1 -> P2 để đạt mức hoàn thiện cao và để bảo vệ đồ án chắc hơn.
