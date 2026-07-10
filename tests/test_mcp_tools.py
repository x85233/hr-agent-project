import importlib
import json
from pathlib import Path

from mcp_server import tools


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TICKETS_PATH = PROJECT_ROOT / "mock_data" / "tickets.json"


def test_search_policy_documents_returns_policy_citations() -> None:
    results = tools.search_policy_documents("PTO accrual full time", top_k=2)

    assert results
    assert results[0]["title"]
    assert results[0]["section"]
    assert results[0]["source"].endswith(".md")
    assert results[0]["snippet"]


def test_get_policy_section_returns_matching_section() -> None:
    result = tools.get_policy_section("pto_policy.md", "PTO Accrual")

    assert result["status"] == "found"
    assert result["source"] == "pto_policy.md"
    assert "15 days" in result["text"]


def test_lookup_employee_profile_returns_jordan_lee() -> None:
    result = tools.lookup_employee_profile("E1001")

    assert result["status"] == "found"
    assert result["employee"]["name"] == "Jordan Lee"


def test_check_pto_balance_returns_low_balance_for_e1003() -> None:
    result = tools.check_pto_balance("E1003")

    assert result["status"] == "found"
    assert result["pto_balance"]["remaining_pto_days"] <= 2


def test_lookup_benefits_status_returns_benefits_data() -> None:
    result = tools.lookup_benefits_status("E1001")

    assert result["status"] == "found"
    assert result["benefits"]["medical"] == "enrolled"
    assert result["benefits"]["retirement_plan"] == "enrolled"


def test_create_mock_hr_ticket_returns_ticket_shape() -> None:
    original_tickets = json.loads(TICKETS_PATH.read_text(encoding="utf-8"))

    try:
        result = tools.create_mock_hr_ticket(
            employee_id="E1001",
            issue_type="PTO",
            summary="Synthetic test ticket from pytest.",
        )

        assert result["ticket_id"].startswith("MOCK-")
        assert result["status"] == "mock_created"
        assert result["summary"] == "Synthetic test ticket from pytest."
    finally:
        TICKETS_PATH.write_text(json.dumps(original_tickets, indent=2), encoding="utf-8")


def test_draft_hr_email_returns_unsent_draft() -> None:
    result = tools.draft_hr_email(
        employee_id="E1001",
        purpose="PTO request follow-up",
    )

    assert result["status"] == "draft_created"
    assert result["sent"] is False
    assert "Jordan Lee" in result["body"]


def test_mcp_server_imports_and_exposes_tool_functions() -> None:
    server_module = importlib.import_module("mcp_server.server")

    assert hasattr(server_module, "create_server")
    assert callable(server_module.search_policy_documents)
    assert callable(server_module.lookup_employee_profile)
