from app.mcp_client import call_tool


def test_call_tool_lookup_employee_profile_returns_jordan_lee() -> None:
    response = call_tool("lookup_employee_profile", {"employee_id": "E1001"})

    assert response["status"] == "ok"
    assert response["result"]["employee"]["name"] == "Jordan Lee"


def test_call_tool_check_pto_balance_returns_pto_data() -> None:
    response = call_tool("check_pto_balance", {"employee_id": "E1003"})

    assert response["status"] == "ok"
    assert response["result"]["pto_balance"]["remaining_pto_days"] <= 2


def test_call_tool_search_policy_documents_returns_citations() -> None:
    response = call_tool(
        "search_policy_documents",
        {"query": "remote work", "top_k": 2},
    )

    assert response["status"] == "ok"
    assert response["result"]
    assert response["result"][0]["source"].endswith(".md")


def test_call_tool_unknown_tool_returns_clear_error() -> None:
    response = call_tool("unknown_tool", {})

    assert response["status"] == "error"
    assert response["error"] == "unknown_tool"
    assert "available_tools" in response
