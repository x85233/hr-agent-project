# HR Agent Project

A beginner-friendly FastAPI skeleton for an agentic HR policy assistant.

The current milestone includes a working web app, a synthetic HR policy corpus, mock employee data, simple keyword retrieval, MCP-exposed tool functions, and a rule-based agent orchestrator.

## Project Structure

```text
hr-agent-project/
  app/
    main.py
    agent.py
    mcp_client.py
    models.py
    static/
      index.html
  rag/
    ingest.py
    retriever.py
  mcp_server/
    server.py
    tools.py
  policies/
    pto_policy.md
    remote_work_policy.md
    ...
  mock_data/
    employees.json
    pto_balances.json
    benefits.json
    tickets.json
  evaluation/
    eval_questions.json
    run_eval.py
    results.md
  tests/
    test_health.py
    test_chat.py
    test_rag.py
    test_mcp_tools.py
    test_agent.py
    test_project_files.py
  requirements.txt
  README.md
  .env.example
  .gitignore
```

## Synthetic Policies and Mock Data

The `policies/` folder contains a synthetic HR policy corpus for a hypothetical company named Acme Horizon. These Markdown files cover PTO, remote work, expenses, benefits, data security, equipment, onboarding, workplace conduct, manager approvals, and travel.

The `mock_data/` folder contains structured synthetic data for employees, PTO balances, benefits, and sample HR tickets. No real employee data is used anywhere in this project.

These files are intended for RAG and tool-calling milestones. The FastAPI app currently uses a simple keyword retriever over the policy files.

## Current RAG Milestone

The app now includes a basic local RAG-style retrieval layer. Policies are loaded from Markdown files in `policies/`, split into chunks by heading, and searched with simple keyword matching.

This milestone does not use embeddings or a vector database. Policy retrieval is also exposed through the local MCP tools described below.

## MCP Tools Milestone

The project includes a local MCP server in `mcp_server/` and plain Python tool functions that are used by the agent orchestrator.

Available MCP tools:

- `search_policy_documents`
- `get_policy_section`
- `lookup_employee_profile`
- `check_pto_balance`
- `lookup_benefits_status`
- `create_mock_hr_ticket`
- `draft_hr_email`

Run the local MCP server with stdio transport:

```bash
python -m mcp_server.server
```

The tools use only synthetic policy and mock HR data. `create_mock_hr_ticket` writes a synthetic ticket to `mock_data/tickets.json`; it does not trigger any real HR workflow.

## Agent Orchestrator Milestone

The `/chat` endpoint now routes messages through a beginner-friendly rule-based orchestrator in `app/agent.py`. The orchestrator classifies the request, calls tools through `app/mcp_client.py`, and returns a final answer with citations and an operational tool trace.

Supported intents and workflows:

- `policy_question`
- `pto_workflow`
- `remote_work_workflow`
- `benefits_workflow`
- `expense_workflow`
- `unknown_or_out_of_scope`

Example prompts:

```text
Can E1003 take PTO next week?
```

```text
Can E1001 work remotely from another country?
```

```text
What benefits does E1002 have?
```

```text
What expenses need director approval?
```

## Demo Prompts

Use these prompts for the polished demo workflows:

```text
Can employee E1001 work remotely from Canada for six weeks?
```

```text
Can employee E1003 take three days of PTO next week? Draft a manager message if appropriate.
```

## MCP Client Architecture

The app now has a clear tool-call path:

```text
FastAPI /chat -> Agent Orchestrator -> MCP Client Layer -> MCP-exposed tools -> RAG/mock data
```

`app/mcp_client.py` provides one public tool-call method:

```python
call_tool(tool_name, arguments)
```

For this milestone, the MCP client is a local adapter that dispatches to the same Python functions exposed by `mcp_server/server.py`. This keeps development reliable while preserving the boundary where a real stdio MCP client can be added later.

The `/health` endpoint reports `mcp_status` and `available_tools`. Each `tool_trace` entry maps to a call made through `app/mcp_client.py`.

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run Locally

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

Open the chat page:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Run Tests

```bash
pytest
```

## Run Evaluation

Run the rule-based evaluation set:

```bash
python evaluation/run_eval.py
```

The evaluation includes 24 synthetic questions and workflow tasks. It reports:

- Total evaluation items
- Tool selection accuracy
- Citation/source match accuracy
- Workflow completion rate
- Out-of-scope guardrail pass rate
- Action-safety pass rate
- Average latency
- p50 latency
- p95 latency

Detailed results are written to `evaluation/eval_results.json`, and summary metrics are written to `evaluation/results.md`.

## CI/CD

GitHub Actions runs on every push and pull request. The CI workflow:

- Checks out the repository
- Sets up Python 3.12
- Installs dependencies from `requirements.txt`
- Checks that the FastAPI app imports
- Checks MCP tool availability through `app.mcp_client.available_tools()`
- Runs `pytest`
- Runs `python evaluation/run_eval.py`
- Uploads evaluation outputs as workflow artifacts

## Current API

`GET /health`

```json
{
  "status": "ok",
  "mcp_status": "connected",
  "available_tools": ["..."]
}
```

`POST /chat`

Request:

```json
{
  "message": "What is the PTO policy?",
  "employee_id": "optional employee ID"
}
```

Response includes an orchestrated answer, policy citations from Markdown chunks when relevant, and a tool trace showing which MCP-exposed tool functions were called.
