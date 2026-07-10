from fastapi.testclient import TestClient

from app.agent import handle_chat
from app.main import app


client = TestClient(app)


def test_pto_workflow_calls_profile_pto_and_policy_tools() -> None:
    result = handle_chat("Can employee E1003 take three days of PTO next week?")
    tool_names = [entry["tool"] for entry in result["tool_trace"]]

    assert "lookup_employee_profile" in tool_names
    assert "check_pto_balance" in tool_names
    assert "search_policy_documents" in tool_names
    assert "2 days remaining" in result["answer"]


def test_remote_work_workflow_returns_citations_and_policy_search() -> None:
    result = handle_chat("Can employee E1001 work remotely from Canada for six weeks?")
    tool_names = [entry["tool"] for entry in result["tool_trace"]]

    assert result["citations"]
    assert "lookup_employee_profile" in tool_names
    assert tool_names.count("search_policy_documents") >= 2
    assert "Summary decision" in result["answer"]
    assert "Required approvals or next steps" in result["answer"]


def test_benefits_workflow_calls_benefits_tool() -> None:
    result = handle_chat("What benefits does E1002 have?")
    tool_names = [entry["tool"] for entry in result["tool_trace"]]

    assert "lookup_benefits_status" in tool_names
    assert "limited" in result["answer"].lower()


def test_missing_employee_id_in_pto_workflow_asks_for_employee_id() -> None:
    result = handle_chat("How much PTO do I have?")

    assert "Please provide an employee ID" in result["answer"]
    assert result["citations"] == []
    assert result["tool_trace"][0]["tool"] == "none"


def test_out_of_scope_question_returns_guardrail() -> None:
    result = handle_chat("What is the best pizza topping?")

    assert "I can help with synthetic Acme Horizon HR policy" in result["answer"]
    assert result["citations"] == []
    assert result["tool_trace"][0]["result_summary"] == "No MCP-exposed tool was called."


def test_chat_uses_orchestrator() -> None:
    response = client.post(
        "/chat",
        json={"message": "Can E1001 work remotely from another country?"},
    )
    data = response.json()
    tool_names = [entry["tool"] for entry in data["tool_trace"]]

    assert response.status_code == 200
    assert data["answer"]
    assert data["citations"]
    assert "lookup_employee_profile" in tool_names
    assert "search_policy_documents" in tool_names


def test_pto_demo_workflow_with_draft_calls_email_tool() -> None:
    result = handle_chat(
        "Can employee E1003 take three days of PTO next week? "
        "Draft a manager message if appropriate."
    )
    tool_names = [entry["tool"] for entry in result["tool_trace"]]

    assert result["citations"]
    assert "lookup_employee_profile" in tool_names
    assert "check_pto_balance" in tool_names
    assert "search_policy_documents" in tool_names
    assert "draft_hr_email" in tool_names
    assert "2 days remaining" in result["answer"]
    assert "3 days requested" in result["answer"]
    assert "Draft manager message" in result["answer"]
