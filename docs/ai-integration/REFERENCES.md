# References

## Tai lieu chinh nen doc

### Structured output

- OpenAI Structured Outputs: https://developers.openai.com/api/docs/guides/structured-outputs
  - Ly do dung: ep AI tra ve JSON dung schema, backend parse/validate de hon.
- OpenAI-compatible chat completions pattern
  - Ly do dung: ds2api/DeepSeek co the duoc boc theo API chat-compatible, giup provider adapter de thay the.

### API/backend

- FastAPI Request Body: https://fastapi.tiangolo.com/tutorial/body/
  - FastAPI dung Pydantic model de validate request body va tu sinh OpenAPI docs.
- FastAPI Background Tasks: https://fastapi.tiangolo.com/tutorial/background-tasks/
  - Co the tham khao cho job execution nhe.
- SQLModel + FastAPI: https://sqlmodel.tiangolo.com/tutorial/fastapi/
  - Phu hop neu muon SQLite schema gon.

### Frontend chot

- React docs: https://react.dev/learn
  - React la thu vien JavaScript de xay UI bang component.
- Monaco Editor: https://microsoft.github.io/monaco-editor/
  - Editor browser-based phu hop trai nghiem giong VSCode.
- `@monaco-editor/react`: https://github.com/suren-atoyan/monaco-react
  - Wrapper tien dung de nhung Monaco vao React.
- Vite: https://vite.dev/
  - Dev server/build tool nhanh cho React frontend.

### Frontend fallback neu can demo nhanh

- Streamlit Chat Elements: https://docs.streamlit.io/develop/api-reference/chat
  - Co `st.chat_input`, `st.chat_message`, hien chart/table nhanh.
- Gradio Code component: https://www.gradio.app/docs/gradio/code
  - Co code editor dung lam input/output, hop voi yeu cau xem-sua code.

### Data AI patterns

- PandasAI: https://docs.pandas-ai.com/
  - Tham khao y tuong hoi-dap voi dataframe, nhung can them approval vi yeu cau mon hoc.
- Jupyter AI: https://github.com/jupyterlab/jupyter-ai
  - Tham khao cach AI ho tro coding/phan tich trong moi truong notebook.
- LangChain Pandas DataFrame Agent: https://api.python.langchain.com/en/latest/experimental/agents/langchain_experimental.agents.agent_toolkits.pandas.base.create_pandas_dataframe_agent.html
  - Tai lieu co security notice ve code nguy hiem. Nen xem de biet vi sao khong cho agent tu chay Python REPL.

### Human-in-the-loop va security

- OpenAI Agents human-in-the-loop: https://openai.github.io/openai-agents-python/human_in_the_loop/
  - Tham khao pattern pause/approve/reject.
- OWASP Top 10 for LLM Applications: https://genai.owasp.org/llmrisk/
  - Tham khao Prompt Injection va Excessive Agency.
- OWASP Logging Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
  - Tham khao log "when, where, who, what".
- OpenTelemetry Logs Data Model: https://opentelemetry.io/docs/specs/otel/logs/data-model/
  - Tham khao trace_id/event/attributes cho logs hien dai.

### Local sandbox

- Docker run reference: https://docs.docker.com/reference/cli/docker/container/run/
- Docker seccomp: https://docs.docker.com/engine/security/seccomp/
- Docker resource constraints: https://docs.docker.com/engine/containers/resource_constraints/

## Repo/pattern dang tham khao

- Judge0: https://github.com/judge0/judge0
  - Open-source code execution system, tham khao model job/result/artifact.
- E2B: https://github.com/e2b-dev/e2b
  - Tham khao sandbox/code interpreter pattern, nhung khong dung truc tiep neu thay yeu cau local-only.
- OpenAI Cookbook: https://github.com/openai/openai-cookbook
  - Tham khao structured outputs, evals, data workflows.

## Ket luan nghien cuu

Huong hien dai nhat khong phai la cho AI agent tu dong dung tool va chay code. Voi yeu cau cua thay, huong dung la:

```text
AI structured proposal -> human review/edit -> approval -> local execution -> audit logs
```

Cach nay vua hop yeu cau mon hoc, vua giong cac pattern human-in-the-loop va least-privilege trong cac tai lieu hien dai.
