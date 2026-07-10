from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["mcp_status"] == "connected"
    assert "search_policy_documents" in data["available_tools"]
    assert "lookup_employee_profile" in data["available_tools"]
