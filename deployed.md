# Deployment Notes

Deployment platform: Render

Planned deployed app URL: TBD

Planned health endpoint: TBD/health

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

This is a single-service deployment containing the FastAPI app, agent orchestrator, MCP client adapter, MCP-exposed tools, policy corpus, RAG retrieval, mock data, and evaluation assets.

Cold-start note: Render free-tier services may spin down after inactivity, so the first request after inactivity may be slower.
