# Software Design Principles For AI Analysis Workbench

## 1. Ket luan kien truc

Huong phu hop nhat cho do an la:

```text
FastAPI backend + React JavaScript frontend + Monaco Editor
```

Day la huong can bang tot giua 4 muc tieu:

- Dung yeu cau cua thay: co API, co frontend, co phe duyet, co execution local, co logs.
- Hien dai: tach frontend/backend, dung structured API, co code editor chuyen nghiep.
- Linh hoat: doi duoc model AI, dataset, cach runner, cach luu log.
- Khong over-engineer: khong can agent framework phuc tap, khong can fine-tune, khong can cai lai toan bo dashboard neu da co.

San pham nen duoc xem la **AI Analysis Workbench**, khong phai chatbot tu dong. AI la tro ly tao de xuat, con nguoi la nguoi quyet dinh.

## 2. Nguyen tac thiet ke cot loi

### 2.1 Separation of Concerns

Moi thanh phan chi nen lam mot nhiem vu ro rang:

- React frontend: hien UI, cho nguoi dung nhap request, xem/sua code, approve, xem result/log.
- FastAPI backend: dieu phoi workflow, validate request, goi AI, luu state.
- AI service: chi tao proposal, khong chay code.
- Approval service: quan ly phe duyet va `code_hash`.
- Execution service: chi chay code da duyet tren local.
- Log service: luu audit trail.

Neu tron cac nhiem vu nay vao nhau, he thong se kho giai thich khi van dap va de vi pham yeu cau "AI khong duoc thuc thi ngam".

### 2.2 Human In The Loop

AI khong duoc tu chay code. Moi code AI sinh ra phai di qua vong:

```text
proposal -> review/edit -> approve -> local execution -> log
```

Thiet ke nay the hien dung vai tro:

- AI: de xuat, viet code, giai thich.
- Con nguoi: xem, sua, phe duyet, quyet dinh.
- He thong: enforce quy trinh, khong dua het niem tin cho UI.

Backend phai enforce state machine, vi frontend co the bi bypass.

### 2.3 API First

Thay khuyen khich tao API, nen backend FastAPI la trung tam. Frontend chi la mot consumer cua API.

Loi ich:

- React, dashboard hien co, notebook, hoac app khac deu co the goi API.
- FastAPI tu sinh OpenAPI docs, de demo va test endpoint.
- Logic approval/execution/logs nam o backend, khong bi khoa vao mot UI.

### 2.4 No Hardcoding

Khong hardcode:

- ten file dataset
- ten cot
- prompt rieng cho mot dataset
- provider AI duy nhat
- output path co dinh
- code mau duy nhat

Thay vao do dung cac lop/khai niem:

- `DatasetRegistry`: quan ly dataset va schema.
- `LLMProvider`: adapter cho DeepSeek/ds2api, OpenAI-compatible, Ollama hoac mock.
- `ProposalService`: tao proposal tu user request + dataset context.
- `ExecutionRunner`: chay code local, co the doi subprocess sang Docker.
- `ArtifactStore`: luu chart/table theo `run_id`.
- `LogStore`: ban dau SQLite, sau co the doi PostgreSQL.
- `PolicyChecker`: validate code truoc khi chay.

### 2.5 Explicit State, Not Implicit Flags

Trang thai proposal/execution nen ro rang:

```text
draft
pending_review
edited
approved
running
succeeded
failed
rejected
```

Khong nen chi dung boolean nhu `isApproved = true`. State ro giup:

- demo de hieu
- logs de truy van
- backend reject dung luc
- bao cao co bang chung

### 2.6 Immutable Audit Trail

Log khong chi de debug. Log la bang chung cho bao cao va van dap.

Moi trace nen luu:

```text
request -> proposal -> edit -> approval -> execution -> result -> explanation
```

Can luu toi thieu:

- user request
- dataset context/schema
- AI code goc
- edited code
- explanation
- approval actor/time
- code hash
- stdout/stderr
- artifacts
- status/error

### 2.7 Local Execution Boundary

Code chi duoc chay tren moi truong local cua nguoi dung. AI provider co the o ngoai, nhung execution phai local.

Execution runner can co:

- working directory rieng theo `run_id`
- output directory rieng
- timeout
- stdout/stderr capture
- import whitelist
- chan shell/network/file system nguy hiem
- khong sua dataset goc

Neu co Docker, co the nang cap sandbox. Neu khong co Docker, subprocess + AST checker + timeout + output directory rieng la du cho demo mon hoc, mien la noi ro gioi han.

## 3. Vi sao FastAPI + React + Monaco la huong tot

### FastAPI

FastAPI phu hop vi:

- dung Python, hop voi pandas/data visualization
- Pydantic validate schema tot
- tu sinh OpenAPI docs
- de tach endpoint AI/proposal/approval/execution/logs
- de chay local

### React JavaScript

React phu hop vi:

- UI component hoa tot
- de lam layout giong VSCode
- de gan vao dashboard web hien co
- linh hoat hon Streamlit/Gradio khi can UI dep
- JavaScript de team frontend tiep can hon TypeScript neu thoi gian gap

### Monaco Editor

Monaco la lua chon dung trong bai nay vi:

- giao dien code editor giong VSCode
- ho tro syntax highlighting Python
- nguoi dung sua code truc tiep
- rat hop voi yeu cau "hien thi code bat buoc" va "nguoi dung co quyen chinh sua"

## 4. Kien truc module de mo rong

```text
frontend/
  src/
    components/
      DatasetSidebar.jsx
      PromptPanel.jsx
      ProposalEditor.jsx
      ApprovalBar.jsx
      ResultViewer.jsx
      LogTimeline.jsx
    api/
      client.js
    App.jsx

backend/
  app/
    api/
      datasets.py
      ai.py
      approvals.py
      executions.py
      logs.py
    services/
      dataset_registry.py
      llm_provider.py
      proposal_service.py
      approval_service.py
      execution_runner.py
      policy_checker.py
      artifact_store.py
      log_store.py
    models/
      schemas.py
      database.py
```

## 5. Interface nen co giua cac lop

### LLMProvider

```text
generate_proposal(user_request, dataset_context) -> Proposal
```

Adapter co the la:

- `DeepSeekProvider`
- `OpenAICompatibleProvider`
- `OllamaProvider`
- `MockProvider` de demo/test khi chua co API key

### ExecutionRunner

```text
run_approved_code(proposal_id, code_hash, dataset_id) -> ExecutionResult
```

Implementation co the la:

- `SubprocessRunner`
- `DockerRunner`

### LogStore

```text
append_event(trace_id, event_type, actor, payload)
get_trace(trace_id) -> events
```

Implementation co the la:

- `SQLiteLogStore`
- `FileLogStore`
- `PostgresLogStore`

## 6. Nhung dieu can tranh

- Khong de React goi truc tiep DeepSeek/OpenAI-compatible provider.
- Khong de AI API goi execution API.
- Khong cho execution API nhan raw code chua approve.
- Khong hardcode cot dataset trong prompt.
- Khong luu moi thu bang screenshot thay cho logs.
- Khong de AI nhan xet so lieu khi chua co artifact.
- Khong de code ghi de dataset goc.
- Khong dua LangChain/PandasAI agent tu chay Python REPL vao demo neu chua co approval boundary.

## 7. Thong diep khi bao ve

> He thong duoc thiet ke theo nguyen ly API-first va human-in-the-loop. AI chi tao proposal gom code va giai thich. Nguoi dung xem, sua va phe duyet. Backend chi cho chay code da approve tren local, dong thoi luu day du audit log. Nhờ tach lop provider, runner, dataset registry va log store, he thong co the doi model AI, doi frontend, doi cach execution ma khong phai viet lai tu dau.
