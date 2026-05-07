# Backend API

FastAPI backend for the AI Analysis Workbench.

## Run

```powershell
cd "D:\Đại học\Năm 3\Data Visualization\FinalTerm"
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## Test

```powershell
python -m pytest backend\tests
```

## Implemented Slice

- `GET /api/datasets`
- `GET /api/datasets/{dataset_id}/context`
- `POST /api/ai/proposals`
- `PATCH /api/ai/proposals/{proposal_id}`
- `POST /api/ai/proposals/{proposal_id}/approve`
- `POST /api/executions`
- `GET /api/logs/{trace_id}`
- API workflow tests in `backend/tests/test_workflow.py`

## Structure

```text
backend/app/
  main.py                 # app setup, CORS, static artifacts, router registration
  schemas.py              # Pydantic request/response contracts
  api/                    # thin FastAPI route handlers
    datasets.py
    proposals.py
    executions.py
    logs.py
  services/               # business rules and workflow orchestration
    dataset_service.py    # DatasetRegistry-style metadata/context loading
    llm_provider.py       # provider interface and provider selection
    mock_llm_provider.py  # replaceable LLMProvider mock implementation
    prompt_builder.py     # system/user prompt and response schema contract
    proposal_service.py   # create, edit, approve, and hash proposals
    execution_runner.py   # local approved-code execution and artifact capture
    policy_checker.py     # AST-based unsafe-code checks
    log_service.py        # audit trace retrieval
  db/
    storage.py            # SQLite persistence and audit events
  core/
    paths.py              # runtime paths and directory creation
```

The backend intentionally keeps route handlers small. State transitions and safety checks live in services so the frontend cannot bypass approval by calling a lower-level endpoint.

## Current Behavior

- AI provider is selected through the `LLMProvider` interface.
- `AI_PROVIDER=mock` is the current local demo provider.
- Prompt builder defines the human-in-the-loop AI rules and structured JSON response schema.
- Execution is local Python subprocess.
- Code must be approved and code hash must match before execution.
- Policy checker blocks unsafe imports, shell/network/file access, direct `df` mutation, and output writes outside `outputs_dir`.
- Execution creates run artifacts under `runs/{run_id}/outputs`.
- SQLite audit data is stored in `ai_logs.db`.

## Next Backend Step

Replace the mock implementation with an `LLMProvider` adapter for Gemini/OpenAI/Ollama while preserving the same proposal schema and approval workflow.

Recommended next implementation order:

1. Add `OpenAIProvider`, `GeminiProvider`, or `OllamaProvider` behind the existing `LLMProvider` interface.
2. Add stronger dataset registration so only configured CSV files can be loaded.
3. Return structured result tables from executions, not only stdout and image artifacts.
4. Add execution timeout and artifact parsing tests.
