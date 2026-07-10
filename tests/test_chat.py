from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_returns_answer_citations_and_tool_trace() -> None:
    response = client.post(
        "/chat",
        json={"message": "How much PTO do I get?", "employee_id": "E123"},
    )

    data = response.json()

    assert response.status_code == 200
    assert data["answer"]
    assert data["citations"]
    assert data["citations"][0]["source"].endswith(".md")
    assert data["tool_trace"]
    tool_names = [entry["tool"] for entry in data["tool_trace"]]
    assert "lookup_employee_profile" in tool_names
    assert "check_pto_balance" in tool_names
    assert "search_policy_documents" in tool_names
