# Deployment Notes

Deployment platform: Render

Deployed app URL: https://hr-agent-project.onrender.com/

Health endpoint: https://hr-agent-project.onrender.com/health

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Architecture note: This is a single-service deployment containing the FastAPI app, agent orchestrator, MCP client adapter, MCP-exposed tools, policy corpus, RAG retrieval, mock data, and evaluation assets.

Health check result:

```json
{
  "status": "ok",
  "mcp_status": "connected",
  "available_tools": [
    "check_pto_balance",
    "create_mock_hr_ticket",
    "draft_hr_email",
    "get_policy_section",
    "lookup_benefits_status",
    "lookup_employee_profile",
    "search_policy_documents"
  ]
}
```

Cold-start note: This app is deployed on Render free tier. The service may spin down after inactivity, so the first request after inactivity may be slower.