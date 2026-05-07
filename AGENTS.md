# AGENTS.md

## Project Direction

This project is an AI-assisted Data Visualization analysis workbench.

The required direction is:

```text
FastAPI backend + React JavaScript frontend + Monaco Editor
```

The app must implement a human-in-the-loop workflow:

```text
user request -> AI proposal -> user review/edit -> approval -> local execution -> logs/results
```

AI must not silently execute code. Human approval is part of the product requirement, not a UI decoration.

## Core Rules

- Do not let AI-generated code run automatically.
- Always show generated code before execution.
- Let the user edit generated code before approval.
- Execute only approved code.
- Run analysis code locally, not in an online/cloud execution environment.
- Do not modify original datasets.
- Do not invent data, columns, charts, images, or analysis results.
- Log all requests, generated code, edited code, explanations, approvals, execution results, errors, and artifacts.

## Architecture Preferences

Use clear module boundaries:

- `DatasetRegistry`: dataset metadata, schema, sample rows, allowed dataset IDs.
- `LLMProvider`: adapter for Gemini, OpenAI, Ollama, or mock provider.
- `ProposalService`: creates AI proposals from user request + dataset context.
- `ApprovalService`: stores review/approval state and code hashes.
- `ExecutionRunner`: executes approved code locally.
- `PolicyChecker`: rejects unsafe code before execution.
- `ArtifactStore`: stores generated tables/charts/log files by `run_id`.
- `LogStore`: stores audit events and trace history.

Avoid hardcoding dataset names, column names, model providers, output paths, or single-use prompts.

## Backend Guidance

Backend should use FastAPI and Pydantic-style schemas.

Recommended API groups:

- `/api/datasets`
- `/api/ai/proposals`
- `/api/ai/proposals/{proposal_id}/approve`
- `/api/executions`
- `/api/logs`

Backend must enforce state transitions. Do not rely on frontend-only checks.

Execution endpoint must reject:

- proposal not approved
- `code_hash` mismatch
- unregistered dataset
- policy checker failure

## Frontend Guidance

Frontend should use React JavaScript.

Use Tailwind CSS for styling and Monaco Editor for the generated Python code editor. The UI should feel like a compact VSCode-style workbench:

- left: dataset/session/log history
- center: prompt, proposal summary, Monaco code editor, approval controls
- right: tabbed inspector with `Result`, `Logs`, and `Policy`

Suggested components:

- `DatasetSidebar.jsx`
- `PromptPanel.jsx`
- `ProposalEditor.jsx`
- `ApprovalBar.jsx`
- `ResultViewer.jsx`
- `LogTimeline.jsx`

## AI Prompting Rules

The AI should return structured proposal data, preferably JSON validated by backend schema.

Proposal should include:

- `summary`
- `code`
- `explanation`
- `assumptions`
- `risk_flags`
- `expected_outputs`

Generated code must assume the input dataframe is named `df`.

Generated code must include Vietnamese comments explaining important operations.

## Execution Safety

Before running code:

- parse/check code with `PolicyChecker`
- allow only approved imports
- block shell/network/filesystem-dangerous functions
- run in a per-run workspace
- write only to output directory
- apply timeout
- capture stdout/stderr

Docker local sandbox is a good upgrade, but the minimum demo can use subprocess + policy checker + timeout + isolated output directory.

## Documentation

Important docs live in:

- `docs/ai-integration/APP.md`
- `docs/ai-integration/SOFTWARE_DESIGN_PRINCIPLES.md`
- `docs/ai-integration/IMPLEMENTATION_GUIDE.md`
- `docs/ai-integration/API_CONTRACT.md`
- `docs/ai-integration/AI_PROMPTS_AND_SCHEMA.md`
- `docs/ai-integration/HUMAN_APPROVAL_EXECUTION.md`
- `docs/ai-integration/LOGS_REPORTING.md`
- `docs/ai-integration/DEMO_QA.md`
- `docs/ai-integration/REQUIREMENT_TRACEABILITY.md`
- `docs/ai-integration/REFERENCES.md`

When editing the project, keep implementation aligned with these documents.
