from mcp_server.tools import (
    check_pto_balance,
    create_mock_hr_ticket,
    draft_hr_email,
    get_policy_section,
    lookup_benefits_status,
    lookup_employee_profile,
    search_policy_documents,
)

try:
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError:
    FastMCP = None


def create_server():
    if FastMCP is None:
        raise RuntimeError(
            "The 'mcp' package is not installed. Run 'pip install -r requirements.txt'."
        )

    server = FastMCP("acme-horizon-hr-tools")

    server.tool()(search_policy_documents)
    server.tool()(get_policy_section)
    server.tool()(lookup_employee_profile)
    server.tool()(check_pto_balance)
    server.tool()(lookup_benefits_status)
    server.tool()(create_mock_hr_ticket)
    server.tool()(draft_hr_email)

    return server


mcp = create_server() if FastMCP is not None else None


def main() -> None:
    if mcp is None:
        raise RuntimeError(
            "The 'mcp' package is not installed. Run 'pip install -r requirements.txt'."
        )

    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print("MCP server stopped.")


if __name__ == "__main__":
    main()
