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
- `POST /api/ai/proposals/jobs`
- `GET /api/ai/proposals/jobs/{job_id}`
- `GET /api/ai/proposals/{proposal_id}`
- `PATCH /api/ai/proposals/{proposal_id}`
- `POST /api/ai/proposals/{proposal_id}/approve`
- `POST /api/ai/proposals/{proposal_id}/reject`
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
    analysis_intent.py    # general prompt intent planner and schema requirement checks
    dataset_capabilities.py # dataset capability inference and feasible analysis suggestions
    dataset_service.py    # DatasetRegistry-style metadata/context loading
    llm_provider.py       # provider interface and provider selection
    mock_llm_provider.py  # replaceable LLMProvider mock implementation
    prompt_builder.py     # system/user prompt and response schema contract
    proposal_service.py   # create, edit, approve, reject, and hash proposals
    execution_runner.py   # local approved-code execution and artifact capture
    policy_checker.py     # AST-based unsafe-code checks
    log_service.py        # audit trace retrieval
  db/
    storage.py            # SQLite persistence and audit events
  core/
    paths.py              # runtime paths and directory creation
```

The backend intentionally keeps route handlers small. State transitions and safety checks live in services so the frontend cannot bypass approval by calling a lower-level endpoint.

Before any real LLM proposal, `analysis_intent.py` classifies the user request into general intents such as distribution, correlation, group comparison, time series, revenue/profit, funnel/conversion, retention, and coordinate map. `dataset_capabilities.py` compares those intents with the selected dataset schema. Missing required capabilities produce a text-only proposal, not an invented chart.

## Current Behavior

- AI provider is selected through the `LLMProvider` interface.
- `AI_PROVIDER=mock` is available for offline demos.
- `AI_PROVIDER=deepseek` and `AI_PROVIDER=openai_compatible` call an OpenAI-compatible chat API.
- ds2api is supported by setting `DEEPSEEK_BASE_URL=http://127.0.0.1:5001`.
- The DeepSeek-compatible provider logs model, finish reason, token usage, cache usage, prompt size, and `llm_duration_ms`.
- Analysis intent preflight checks the prompt against dataset capabilities before calling the LLM.
- Prompt builder defines the human-in-the-loop AI rules and structured JSON response schema.
- Execution is local Python subprocess.
- Code must be approved and code hash must match before execution.
- Policy checker blocks unsafe imports, shell/network/file access, direct `df` mutation, and output writes outside `outputs_dir`.
- Execution creates run artifacts under `runs/{run_id}/outputs`.
- SQLite audit data is stored in `ai_logs.db`.

## DeepSeek / ds2api Configuration

Recommended fast local ds2api settings:

```env
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_ds2api_key
DEEPSEEK_BASE_URL=http://127.0.0.1:5001
DEEPSEEK_MODEL=deepseek-v4-flash-nothinking
DEEPSEEK_INSIGHT_MODEL=deepseek-v4-flash-nothinking
DS2API_TARGET_ACCOUNT=
DEEPSEEK_APPEND_V1=true
DEEPSEEK_MAX_TOKENS=2200
DEEPSEEK_INSIGHT_MAX_TOKENS=900
DEEPSEEK_TEMPERATURE=0.2
DEEPSEEK_TIMEOUT_SECONDS=60
DEEPSEEK_THINKING=disabled
AI_FALLBACK_TO_MOCK_ON_ERROR=false
AI_EXPLAIN_RESULT_ENABLED=true
AI_EXPLAIN_RESULT_PROVIDER=deepseek
AI_EXPLAIN_RESULT_TIMEOUT_SECONDS=45
EXECUTION_TIMEOUT_SECONDS=60
PROPOSAL_JOB_MAX_CONCURRENCY=1
```

`DEEPSEEK_BASE_URL` accepts either a root URL (`http://127.0.0.1:5001`) or a full OpenAI-compatible URL ending in `/v1`. The backend will not duplicate `/v1`.
`DEEPSEEK_MODEL` is used for code proposals. Keep `AI_FALLBACK_TO_MOCK_ON_ERROR=false` for real demos so provider failures are visible instead of producing fake mock code.
`DS2API_TARGET_ACCOUNT` is optional. Set it to an email such as `student@example.com` when you want ds2api managed-account mode to use a specific account instead of rotating across all configured accounts.
`AI_EXPLAIN_RESULT_PROVIDER=deepseek` makes ds2api/DeepSeek write the post-execution insight from real stdout, table previews, and artifact metadata. Charts are displayed to the user as visual illustration; they are not the source of numeric truth for the model. The insight prompt is evidence-only and does not send the full generated code into the commentary step.

The repository includes an optional local Docker setup under `ds2api/`. Copy `ds2api/.env.example` to `ds2api/.env`, copy `ds2api/config.example.json` to `ds2api/config.json`, add real account/key values, then run `docker compose up -d` from the `ds2api` folder.

Quick connectivity test after Docker ds2api is running:

```powershell
Invoke-WebRequest http://127.0.0.1:5001/v1/models -UseBasicParsing
python -m backend.scripts.test_llm_provider
```

If the test returns `401 Invalid token`, add the same `DEEPSEEK_API_KEY` value to ds2api `config.keys` or update `.env` to match a key already allowed by ds2api.

## Next Backend Step

Add optional streaming or background proposal jobs if generation latency still feels slow after inspecting `llm_duration_ms` in the audit log.

Recommended next implementation order:

1. Add proposal polling/streaming for better perceived latency.
2. Add stronger dataset registration so only configured CSV files can be loaded.
3. Return structured result tables from executions, not only stdout and image artifacts.
4. Add execution timeout and artifact parsing tests.
