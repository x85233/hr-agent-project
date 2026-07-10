from collections.abc import Callable
from typing import Any

from mcp_server import tools


# Milestone 6 uses a local adapter for reliability: these functions are exposed
# by the MCP server, and the app calls them only through this client boundary.
# A later milestone can replace this dispatcher with a real stdio MCP client.
TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    "search_policy_documents": tools.search_policy_documents,
    "get_policy_section": tools.get_policy_section,
    "lookup_employee_profile": tools.lookup_employee_profile,
    "check_pto_balance": tools.check_pto_balance,
    "lookup_benefits_status": tools.lookup_benefits_status,
    "create_mock_hr_ticket": tools.create_mock_hr_ticket,
    "draft_hr_email": tools.draft_hr_email,
}


def available_tools() -> list[str]:
    return sorted(TOOL_REGISTRY)


def call_tool(tool_name: str, arguments: dict) -> dict:
    tool = TOOL_REGISTRY.get(tool_name)

    if tool is None:
        return {
            "status": "error",
            "error": "unknown_tool",
            "tool": tool_name,
            "message": f"Tool '{tool_name}' is not available.",
            "available_tools": available_tools(),
        }

    try:
        result = tool(**arguments)
    except TypeError as error:
        return {
            "status": "error",
            "error": "invalid_arguments",
            "tool": tool_name,
            "message": str(error),
        }

    return {
        "status": "ok",
        "tool": tool_name,
        "result": result,
    }
