# Design and Evaluation

## 1. Project Overview

This project is a synthetic HR policy assistant for a hypothetical company named Acme Horizon. It is an educational project and does not use real employee data or real company policy data.

The system combines a FastAPI web app, lightweight RAG over synthetic Markdown policy documents, a rule-based agent orchestrator, MCP-exposed tools, mock structured HR data, evaluation assets, and a deployed chat interface.

## 2. Architecture

The application follows a layered architecture:

```text
FastAPI web app
  -> /chat endpoint
  -> agent orchestrator
  -> MCP client adapter
  -> MCP-exposed tools
  -> RAG retriever and mock HR data
```

The deployed Render service is a single Python web service. It contains the FastAPI app, static chat page, agent logic, MCP client adapter, MCP tool functions, policy corpus, mock data, and evaluation files in one deployable project.

```text
Browser chat UI
  -> Render FastAPI service
    -> app.main:/chat
      -> app.agent.handle_chat
        -> app.mcp_client.call_tool
          -> mcp_server.tools
            -> rag.retriever / mock_data JSON
```

## 3. RAG Design

Policy documents are stored as Markdown files in `policies/`. Each file represents a synthetic Acme Horizon HR policy, such as PTO, remote work, expenses, benefits, travel, workplace conduct, and data security.

The ingestion layer loads Markdown files and chunks them by heading. Each chunk preserves citation metadata:

- Policy title
- Section heading
- Source file
- Snippet text

Retrieval is keyword-based in this version. The retriever scores chunks by keyword overlap between the user query and the chunk title, section, source, and text. This approach is intentionally lightweight, deterministic, easy to test, and compatible with free-tier deployment because it does not require embeddings, a vector database, or external model calls.

## 4. MCP Server and Tool Design

The project defines MCP-exposed tools in `mcp_server/tools.py` and exposes them through a local MCP server in `mcp_server/server.py`.

Available tools:

- `search_policy_documents`: Searches policy chunks and returns relevant citations.
- `get_policy_section`: Retrieves a specific section from a policy source file.
- `lookup_employee_profile`: Looks up a synthetic employee profile from `mock_data/employees.json`.
- `check_pto_balance`: Looks up synthetic PTO balance data from `mock_data/pto_balances.json`.
- `lookup_benefits_status`: Looks up synthetic benefits data from `mock_data/benefits.json`.
- `create_mock_hr_ticket`: Creates a synthetic mock ticket in `mock_data/tickets.json`.
- `draft_hr_email`: Drafts an HR-related email but does not send it.

The web app routes tool calls through `app/mcp_client.py`. For this milestone, the MCP client is a reliable local adapter that dispatches to the MCP-exposed Python functions. The `/health` endpoint exposes MCP connection status and the list of available tools.

## 5. Agent Orchestration

The agent orchestrator in `app/agent.py` uses controlled rule-based routing. This keeps behavior predictable, testable, and easy to inspect for grading.

Supported intents and workflows:

- `policy_question`
- `pto_workflow`
- `remote_work_workflow`
- `benefits_workflow`
- `expense_workflow`
- `ambiguous_request`
- `out_of_scope_request`
- `action_safety`

Responses include:

- `answer`: A user-facing response.
- `citations`: Retrieved policy citations when relevant.
- `tool_trace`: A clear trace of which MCP-exposed tools were called and with what arguments.

## 6. Safety and Guardrails

The assistant is limited to synthetic Acme Horizon HR policy and workflow questions. Out-of-scope questions are redirected to supported HR topics.

Workflow requests that require employee context ask for an employee ID when one is missing. This prevents the assistant from inventing employee-specific data.

Actions are mock-only. `draft_hr_email` creates an unsent draft and clearly states that no email was sent. `create_mock_hr_ticket` creates only a synthetic ticket in local mock data and does not trigger any real HR workflow.

## 7. Demo Workflows

Remote work demo:

```text
Can employee E1001 work remotely from Canada for six weeks?
```

Expected tools:

- `lookup_employee_profile`
- `search_policy_documents`
- `search_policy_documents`

PTO demo:

```text
Can employee E1003 take three days of PTO next week? Draft a manager message if appropriate.
```

Expected tools:

- `lookup_employee_profile`
- `check_pto_balance`
- `search_policy_documents`
- `draft_hr_email`

## 8. Evaluation Method

The evaluation set is stored in `evaluation/eval_questions.json` and contains 24 items.

Covered categories include:

- `simple_policy_question`
- `multi_document_policy_question`
- `pto_workflow`
- `remote_work_workflow`
- `benefits_workflow`
- `expense_workflow`
- `ambiguous_request`
- `out_of_scope_request`
- `action_safety`

The script `evaluation/run_eval.py` runs each question through `app.agent.handle_chat`. It uses rule-based checks rather than an LLM judge.

Checks include:

- Expected tool use
- Expected source and citation matches
- Workflow completion
- Guardrail behavior
- Action safety
- Latency

## 9. Evaluation Results

Actual evaluation results:

- Total evaluation items: 24
- Tool selection accuracy: 100.0%
- Citation/source match accuracy: 95.0%
- Workflow completion rate: 100.0%
- Out-of-scope guardrail pass rate: 100.0%
- Action-safety pass rate: 100.0%
- Average latency: 8.92 ms
- p50 latency: 9.22 ms
- p95 latency: 16.67 ms

## 10. CI/CD and Deployment

GitHub Actions runs on push and pull request. The workflow installs dependencies, checks that the FastAPI app imports, checks MCP tool availability, runs `pytest`, and runs the evaluation script.

The app is deployed on Render:

```text
https://hr-agent-project.onrender.com/
```

Health endpoint:

```text
https://hr-agent-project.onrender.com/health
```

This is a Render free-tier deployment, so the service may spin down after inactivity. The first request after inactivity may be slower because of cold start behavior.

## 11. Troubleshooting Notes

During development, several reproducibility and CI/CD issues were found and fixed:

- Fixed a GitHub Actions path issue caused by an incorrect `working-directory`.
- Fixed pytest import issues by adding `pytest.ini` with `pythonpath = .`.
- Fixed evaluation artifact upload paths so CI uploads the correct files.

These fixes improved repeatability across local development, GitHub Actions, and deployment environments.
