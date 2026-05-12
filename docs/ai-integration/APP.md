# APP: AI Data Analysis Workbench

## 1. Mục Tiêu

Ứng dụng này là một workbench phân tích dữ liệu có AI hỗ trợ, xây dựng theo hướng:

```text
FastAPI backend + React JavaScript frontend + Monaco Editor
```

Mục tiêu chính không phải là để AI tự chạy phân tích, mà là tạo một quy trình có con người kiểm soát:

```text
User request -> AI proposal -> User review/edit -> Approval -> Local execution -> Logs/results
```

Luồng này bám sát yêu cầu của giảng viên:

- AI chỉ đề xuất hướng phân tích, sinh code và giải thích code.
- Người dùng xem, chỉnh sửa và quyết định có chạy code hay không.
- Code chỉ chạy sau khi được phê duyệt.
- Code chạy ở máy local, không chạy trên môi trường online.
- Dữ liệu gốc không bị sửa.
- Toàn bộ request, code, approval, kết quả, lỗi và artifact được lưu lại.

## 2. Kiến Trúc Tổng Quan

Hệ thống chia thành ba lớp rõ ràng.

### Frontend

Frontend dùng React JavaScript, Tailwind CSS và Monaco Editor. Giao diện theo kiểu VSCode-style workbench:

- Sidebar trái: dataset, schema, session/history.
- Editor trung tâm: code Python do AI sinh ra, cho phép người dùng sửa trước khi duyệt.
- Sidebar/Panel thao tác: prompt, proposal summary, approval/reject/run local.
- Inspector/Bottom panel: result, logs, policy.

Frontend không được tự quyết định trạng thái bảo mật. Nó chỉ gửi thao tác người dùng về backend. Backend mới là nơi enforce approval, code hash và policy.

### Backend

Backend dùng FastAPI, Pydantic schema và SQLite. Backend chịu trách nhiệm:

- Đọc metadata dataset đã đăng ký.
- Tạo context an toàn cho AI: schema, dtype, null count, sample values.
- Gọi LLM provider để tạo proposal.
- Lưu proposal ở trạng thái `pending_review`.
- Nhận code đã chỉnh sửa và phê duyệt từ người dùng.
- Kiểm tra policy trước khi chạy.
- Chạy code local trong workspace riêng theo `run_id`.
- Thu thập stdout, stderr, chart/table artifact.
- Gọi ds2api/DeepSeek để nhận xét từ stdout, bảng artifact và metadata thật sau khi execution thành công.
- Ghi audit log cho toàn bộ luồng.

Trước khi gọi LLM, backend chạy lớp `AnalysisIntentPlanner`: phân loại yêu cầu thành các intent tổng quát như phân bố, tương quan, so sánh nhóm, chuỗi thời gian, doanh thu/lợi nhuận, funnel/conversion, retention hoặc bản đồ tọa độ. Planner đối chiếu intent với capability thật của dataset. Nếu thiếu cột bắt buộc, backend tạo proposal text-only giải thích thiếu schema, không để AI tự bịa cột hoặc tự chuyển sang biểu đồ khác.

### Local Storage

Ứng dụng dùng:

- SQLite để lưu proposal, approval, execution và audit event.
- Thư mục `runs/{run_id}/outputs` để lưu artifact sinh ra sau execution.
- Dataset gốc nằm ngoài output workspace và không bị ghi đè.

## 3. API Chính

API hiện tại dùng nhóm endpoint rõ ràng, không dùng API cũ kiểu `/api/generate-code` hoặc `/api/execute-code`.

### Dataset API

```text
GET /api/datasets
GET /api/datasets/{dataset_id}/context
```

Dùng để frontend lấy danh sách dataset, schema, dtype, null count và sample values.

### AI Proposal API

```text
POST /api/ai/proposals/jobs
GET  /api/ai/proposals/jobs/{job_id}
POST /api/ai/proposals
GET  /api/ai/proposals/{proposal_id}
PATCH /api/ai/proposals/{proposal_id}
POST /api/ai/proposals/{proposal_id}/approve
POST /api/ai/proposals/{proposal_id}/reject
```

AI proposal phải có cấu trúc:

- `summary`
- `code`
- `explanation`
- `assumptions`
- `risk_flags`
- `expected_outputs`

Code do AI sinh ra phải giả định dataframe đầu vào là `df`, output folder là `outputs_dir`, và phải có comment tiếng Việt cho các thao tác quan trọng. AI chỉ được dùng tên cột có trong dataset context; nếu yêu cầu cần cột không tồn tại thì phải tạo proposal text-only để giải thích và gợi ý hướng thay thế, không được giả định cột rồi chạy “thành công giả”.

### Execution API

```text
POST /api/executions
```

Execution endpoint chỉ nhận code đã được phê duyệt. Backend sẽ từ chối nếu:

- Proposal chưa được approve.
- `code_hash` không khớp code đã approve.
- Dataset không hợp lệ.
- Policy checker phát hiện hành vi không an toàn.

Response execution gồm:

- `status`
- `stdout`
- `stderr`
- `artifacts`
- `ai_insight`
- `ai_insight_status`
- `ai_insight_error`
- `return_code`
- `duration_ms`

### Logs API

```text
GET /api/logs/{trace_id}
```

Logs dùng để chứng minh hệ thống có lưu lại toàn bộ quá trình: request, proposal, edit, approval, execution, lỗi, artifact và AI insight.

## 4. Luồng Human-In-The-Loop

### Bước 1: Người dùng chọn dataset

Backend trả metadata dataset. AI chỉ nhận context rút gọn, không nhận toàn bộ file dữ liệu gốc.

### Bước 2: Người dùng nhập yêu cầu phân tích

Ví dụ:

```text
Vẽ biểu đồ doanh thu theo tháng và nhận xét xu hướng chính.
```

### Bước 3: AI tạo proposal

Backend gửi prompt gồm yêu cầu người dùng, schema và luật runtime cho LLM. AI trả về JSON proposal. Code chưa chạy ở bước này.

### Bước 4: Người dùng review và chỉnh sửa code

Monaco Editor hiển thị code Python. Người dùng có thể sửa tham số, đổi loại biểu đồ, đổi cách group dữ liệu hoặc reject proposal.

### Bước 5: Người dùng approve

Backend lưu approval, code hash và audit event. Đây là bằng chứng rằng người dùng là người quyết định.

### Bước 6: Run local

Backend kiểm tra lại state, code hash và policy. Nếu hợp lệ, code được chạy local trong `runs/{run_id}`.

### Bước 7: Hiển thị result và log

Frontend hiển thị stdout, stderr, chart/table artifact và audit logs.

### Bước 8: AI nhận xét từ số liệu local

Sau khi execution thành công, backend gửi stdout, preview bảng artifact và metadata artifact cho ds2api/DeepSeek theo prompt evidence-only. AI chỉ được nhận xét dựa trên:

- Stdout thật.
- Preview bảng artifact thật.
- Metadata artifact.

Insight prompt không gửi code dài vào bước nhận xét và cấm nhắc tên nhóm/địa danh/cột nếu chuỗi đó không xuất hiện nguyên văn trong evidence. Biểu đồ vẫn được tạo và hiển thị như minh họa trực quan cho người dùng, nhưng không phải nguồn số liệu chính cho nhận xét AI. Nếu execution thành công nhưng không có stdout, bảng hoặc artifact thật thì AI insight ở trạng thái `not_requested`. Nếu code có lệnh tạo artifact như `savefig()` nhưng cuối cùng không tạo chart/table thật, backend đánh dấu execution là `failed` để tránh thành công giả. Nếu ds2api/DeepSeek lỗi hoặc timeout sau khi execution thành công, execution vẫn thành công và UI hiển thị trạng thái insight tương ứng.

## 5. Nguyên Tắc An Toàn

Policy checker chặn các nhóm hành vi sau:

- Import module nguy hiểm như `os`, `subprocess`, `socket`, `requests`, `urllib`, `shutil`, `pickle`.
- Gọi shell/network/filesystem nguy hiểm.
- Đọc thêm file dữ liệu ngoài dataset đã nạp.
- Ghi file ngoài `outputs_dir / "ten_file.ext"`.
- Sửa trực tiếp `df` gốc hoặc dùng `inplace=True` trên dữ liệu gốc.
- Truy cập nội bộ kiểu `__dunder__`.

Policy không nhằm chặn việc phân tích/vẽ biểu đồ hợp lệ. Các thư viện phân tích/visualization được phép gồm `pandas`, `numpy`, `matplotlib`, `matplotlib.dates`, `matplotlib.ticker`, `seaborn`, `scipy.stats`, `scipy.optimize`, `scipy.signal`, `sklearn.metrics`, `sklearn.model_selection`, `sklearn.preprocessing`, `sklearn.linear_model`, `statsmodels.api`, `statsmodels.formula.api`, `statsmodels.tsa`, `math`, `statistics`, `datetime`, `collections`. Các nhánh có thể đọc dữ liệu ngoài như `scipy.io`, `sklearn.datasets`, `statsmodels.datasets` vẫn bị chặn.

## 6. Cấu Hình AI

Ví dụ cấu hình ds2api:

```env
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_ds2api_key
DEEPSEEK_BASE_URL=http://127.0.0.1:5001
DEEPSEEK_MODEL=deepseek-v4-flash-nothinking
DEEPSEEK_INSIGHT_MODEL=deepseek-v4-flash-nothinking
DEEPSEEK_APPEND_V1=true
DEEPSEEK_MAX_TOKENS=2200
DEEPSEEK_INSIGHT_MAX_TOKENS=900
DEEPSEEK_TEMPERATURE=0.2
DEEPSEEK_TIMEOUT_SECONDS=60
AI_EXPLAIN_RESULT_ENABLED=true
AI_EXPLAIN_RESULT_PROVIDER=deepseek
AI_EXPLAIN_RESULT_TIMEOUT_SECONDS=45
EXECUTION_TIMEOUT_SECONDS=60
```

Model sinh code và model nhận xét kết quả có thể dùng cùng ds2api hoặc tách bằng `DEEPSEEK_INSIGHT_MODEL`. Nếu provider nhận xét bị lỗi, hệ thống chỉ đánh dấu `ai_insight_status=failed`, không làm hỏng kết quả execution.

## 7. Điểm Cần Nhấn Mạnh Khi Vấn Đáp

- AI không tự chạy code, chỉ tạo proposal.
- Con người bắt buộc xem code và approve.
- Backend enforce approval bằng trạng thái proposal và `code_hash`, không tin frontend.
- Code chạy local trên máy người dùng.
- Dữ liệu gốc không bị ghi đè.
- Output chỉ được ghi vào thư mục run riêng.
- Mọi thứ có audit log để truy xuất lại.
- AI nhận xét sau execution dựa trên stdout/bảng/artifact thật, không được bịa số liệu; biểu đồ chỉ là minh họa trực quan.
