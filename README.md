# AI Analysis Workbench

An AI-assisted data analysis workbench for Data Visualization projects.

The application follows a strict human-in-the-loop workflow:

```text
user request -> AI proposal -> user review/edit -> approval -> local execution -> logs/results
```

AI is used to suggest analysis ideas, generate Python analysis code, and explain approved outputs. It does **not** execute code silently, modify original datasets, or invent data, columns, charts, images, or results.

## Why This Project Exists

This project was built for an AI integration requirement in a Data Visualization final project. The central idea is not to attach a chatbot to a dashboard, but to build a controlled analysis workflow where:

- AI helps propose and write analysis code.
- Humans review, edit, and approve the code.
- Approved code runs locally on the user's machine.
- Every request, proposal, approval, execution, result, error, and artifact is logged for review.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | FastAPI, Pydantic, SQLite |
| Frontend | React, JavaScript, Vite |
| Styling | Tailwind CSS |
| Code editor | Monaco Editor |
| AI provider | Mock, DeepSeek, or OpenAI-compatible API such as ds2api |
| Analysis runtime | Local Python subprocess |
| Data/Charts | pandas, matplotlib |
| Tests | pytest |

## Core Safety Rules

- AI-generated code is always shown before execution.
- Users can edit generated code before approval.
- Execution is allowed only after human approval.
- Execution must happen locally, not in an online/cloud runner.
- Original datasets must not be modified.
- Generated code must use the input dataframe as `df`.
- Generated code must copy data with `work_df = df.copy()` before transformations.
- Output artifacts must be written only to `outputs_dir`.
- Unsafe imports, shell/network/file operations, and direct mutation of `df` are blocked by the backend policy checker.

## Architecture

```text
React Frontend
  - Dataset/sidebar context
  - Prompt input
  - Monaco code editor
  - Approval controls
  - Result, Policy, and Logs inspector
        |
        v
FastAPI Backend
  - Dataset API
  - AI Proposal API
  - Approval API
  - Local Execution API
  - Logs API
        |
        v
Local Python Runner
  - Loads registered dataset as df
  - Runs approved code only
  - Captures stdout/stderr
  - Stores artifacts under runs/{run_id}/outputs
        |
        v
SQLite Audit Log
```

## Repository Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routers
│   │   ├── core/             # runtime paths/config helpers
│   │   ├── db/               # SQLite storage
│   │   ├── services/         # business logic and safety rules
│   │   ├── main.py           # FastAPI app setup
│   │   └── schemas.py        # Pydantic contracts
│   ├── tests/                # pytest workflow tests
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── api/              # API client
│   │   ├── components/       # workbench UI components
│   │   ├── App.jsx
│   │   └── styles.css
│   ├── package.json
│   └── vite.config.js
├── docs/ai-integration/      # design, API, prompts, demo, traceability docs
├── PHANCONG.md               # team task split
└── AGENTS.md                 # project guidance for coding agents
```

## Dataset Visibility Rule

Datasets shown in the frontend dataset list are controlled by `backend/config/datasets.json`.

Each registered dataset can include:

- `allowed`: backend allowlist for dataset usage
- `visible`: whether the dataset appears in the frontend selector

Example:

```json
{
  "id": "vietnam_real_estate_cleaned",
  "path": "cleaned_vietnam_real_estate.csv",
  "allowed": true,
  "visible": true
}
```

## Backend Modules

| Module | Responsibility |
| --- | --- |
| `DatasetRegistry` / `dataset_service.py` | Dataset metadata, schema, sample values, allowed dataset IDs |
| `LLMProvider` / `llm_provider.py` | Adapter boundary for mock, Gemini, OpenAI, or Ollama providers |
| `prompt_builder.py` | Prompt rules and structured proposal schema |
| `proposal_service.py` | Create, edit, approve, reject, and hash AI proposals |
| `policy_checker.py` | AST-based unsafe-code validation |
| `execution_runner.py` | Local approved-code execution and artifact capture |
| `storage.py` | SQLite persistence for proposals, approvals, executions, and audit events |
| `log_service.py` | Trace/audit retrieval |

## API Overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/datasets` | List registered datasets |
| `GET` | `/api/datasets/{dataset_id}/context` | Get dataset schema/context |
| `POST` | `/api/ai/proposals` | Create an AI analysis proposal |
| `POST` | `/api/ai/proposals/jobs` | Start background AI proposal generation |
| `GET` | `/api/ai/proposals/jobs/{job_id}` | Poll background generation status |
| `GET` | `/api/ai/proposals/{proposal_id}` | Get a generated proposal |
| `PATCH` | `/api/ai/proposals/{proposal_id}` | Save user-edited code |
| `POST` | `/api/ai/proposals/{proposal_id}/approve` | Approve the current code and generate a hash |
| `POST` | `/api/ai/proposals/{proposal_id}/reject` | Reject a proposal and save the decision in logs |
| `POST` | `/api/executions` | Run approved code locally |
| `GET` | `/api/logs/{trace_id}` | Retrieve audit events for a trace |

FastAPI docs are available after starting the backend:

```text
http://127.0.0.1:8000/docs
```

## Getting Started

### 1. Backend

```powershell
python -m venv .venv
./.venv/bin/python -m pip install -r backend/requirements.txt
cp .env.example .env
# edit .env and set DEEPSEEK_API_KEY / ds2api key, or set AI_PROVIDER=mock for offline demo
set -a
source .env
set +a
./.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

The backend creates demo CSV files and runtime folders locally when needed. These generated files are ignored by Git.

Recommended ds2api settings:

```env
AI_PROVIDER=deepseek
DEEPSEEK_BASE_URL=http://127.0.0.1:5001
DEEPSEEK_MODEL=deepseek-v4-flash-nothinking
DEEPSEEK_MAX_TOKENS=2200
DEEPSEEK_TIMEOUT_SECONDS=60
DEEPSEEK_THINKING=disabled
```

Each generated proposal audit log includes `llm_duration_ms`, model, finish reason, prompt size, and token/cache usage when the provider returns it.

### 2. Frontend

```powershell
npm install --prefix frontend
npm run dev --prefix frontend
```

Open:

```text
http://127.0.0.1:5173
```

## Running Checks

Backend tests:

```powershell
./.venv/bin/python -m pytest backend/tests
```

Frontend production build:

```powershell
npm run build --prefix frontend
```

Dependency audit:

```powershell
npm audit --audit-level=moderate --prefix frontend
```

## Demo Flow

1. Start the backend and frontend.
2. Select a dataset.
3. Enter an analysis request.
4. Generate an AI proposal.
5. Review and edit the generated Python code in Monaco Editor.
6. Approve the code.
7. Run the approved code locally.
8. Inspect chart artifacts, stdout/stderr, policy status, and audit logs.

## Current Status

Implemented:

- FastAPI backend structure with clear API/service/db boundaries.
- VSCode-style React workbench UI following the main workbench containers: Title Bar, Activity Bar, Primary Sidebar, Editor, bottom Panel, Secondary Sidebar chat, and Status Bar.
- Mock AI provider behind an `LLMProvider` boundary.
- DeepSeek/OpenAI-compatible provider with ds2api-friendly configuration and latency/token logging.
- Prompt builder and structured proposal schema.
- Human approval workflow with code hash validation.
- Local Python execution runner.
- AST-based policy checker.
- SQLite audit logging.
- Backend workflow tests.
- GitHub-ready cleanup and `.gitignore`.

Next recommended work:

- Add streaming or background proposal jobs if AI generation still feels slow.
- Move dataset registration from hardcoded metadata to a config file.
- Return structured table artifacts, not only stdout/chart images.
- Display backend policy errors directly in the frontend Policy tab.
- Add end-to-end frontend tests.

## Documentation

Detailed design documents live in:

```text
docs/ai-integration/
```

Important files:

- `APP.md`
- `SOFTWARE_DESIGN_PRINCIPLES.md`
- `IMPLEMENTATION_GUIDE.md`
- `API_CONTRACT.md`
- `AI_PROMPTS_AND_SCHEMA.md`
- `HUMAN_APPROVAL_EXECUTION.md`
- `LOGS_REPORTING.md`
- `DEMO_QA.md`
- `REQUIREMENT_TRACEABILITY.md`
- `REFERENCES.md`

## Team Work Split

See:

```text
PHANCONG.md
```

## License

This repository is currently intended for academic project use. Add a license file before public reuse or distribution.
