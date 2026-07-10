import re
from typing import Any

from app.mcp_client import call_tool


EMPLOYEE_ID_PATTERN = re.compile(r"\bE\d{4}\b", re.IGNORECASE)
NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def handle_chat(message: str, employee_id: str | None = None) -> dict:
    resolved_employee_id = employee_id or _extract_employee_id(message)
    intent = _classify_intent(message, has_employee_id=resolved_employee_id is not None)

    if intent == "pto_workflow":
        return _handle_pto_workflow(message, resolved_employee_id)

    if intent == "remote_work_workflow":
        return _handle_remote_work_workflow(resolved_employee_id)

    if intent == "benefits_workflow":
        return _handle_benefits_workflow(resolved_employee_id)

    if intent == "expense_workflow":
        return _handle_expense_workflow(message)

    if intent == "policy_question":
        return _handle_policy_question(message)

    return {
        "answer": (
            "I can help with synthetic Acme Horizon HR policy and workflow questions. "
            "Please ask about PTO, remote work, benefits, expenses, onboarding, "
            "equipment, conduct, or travel."
        ),
        "citations": [],
        "tool_trace": [
            {
                "tool": "none",
                "arguments": {"intent": "unknown_or_out_of_scope"},
                "result_summary": "No MCP-exposed tool was called.",
            }
        ],
    }


def _classify_intent(message: str, has_employee_id: bool = False) -> str:
    text = message.lower()

    if _has_word(text, "pto") or _has_any(
        text,
        ["vacation", "time off", "leave balance", "sick leave"],
    ):
        if not has_employee_id and _has_any(
            text,
            ["policy", "accrue", "accrual", "allowance", "full-time employees"],
        ):
            return "policy_question"
        return "pto_workflow"

    if _has_any(text, ["remote", "work from home", "hybrid", "abroad", "another country"]):
        if not has_employee_id and _has_any(text, ["policy", "approval", "security"]):
            return "policy_question"
        return "remote_work_workflow"

    if _has_any(text, ["benefit", "medical", "dental", "vision", "401", "retirement"]):
        return "benefits_workflow"

    if _has_any(text, ["expense", "reimbursement", "receipt", "meal", "mileage"]):
        return "expense_workflow"

    if _has_any(
        text,
        [
            "policy",
            "onboarding",
            "equipment",
            "laptop",
            "conduct",
            "travel",
            "approval",
            "security",
            "holiday",
        ],
    ):
        return "policy_question"

    return "unknown_or_out_of_scope"


def _handle_policy_question(message: str) -> dict:
    results = _call_search_policy_documents(message, top_k=3)

    return {
        "answer": _policy_answer(results),
        "citations": _citations_from_results(results),
        "tool_trace": [
            _trace_policy_search(message, 3, results),
        ],
    }


def _handle_pto_workflow(message: str, employee_id: str | None) -> dict:
    if not employee_id:
        return _missing_employee_id_response("PTO")

    profile = _call_lookup_employee_profile(employee_id)
    pto_balance = _call_check_pto_balance(employee_id)
    results = _call_search_policy_documents(
        "PTO accrual approval requirements advance notice request balance",
        top_k=3,
    )
    requested_days = _extract_requested_days(message)
    draft_email = None

    if _wants_draft(message):
        draft_email = _call_draft_hr_email(
            employee_id=employee_id,
            purpose="PTO request guidance",
            recipient_type="manager",
        )

    answer = _pto_answer(
        employee_id=employee_id,
        profile=profile,
        pto_balance=pto_balance,
        results=results,
        requested_days=requested_days,
        draft_email=draft_email,
    )
    tool_trace = [
        _trace_employee_profile(employee_id, profile),
        _trace_pto_balance(employee_id, pto_balance),
        _trace_policy_search(
            "PTO accrual approval requirements advance notice request balance",
            3,
            results,
        ),
    ]

    if draft_email:
        tool_trace.append(_trace_draft_hr_email(employee_id, draft_email))

    return {
        "answer": answer,
        "citations": _citations_from_results(results),
        "tool_trace": tool_trace,
    }


def _handle_remote_work_workflow(employee_id: str | None) -> dict:
    if not employee_id:
        return _missing_employee_id_response("remote work")

    profile = _call_lookup_employee_profile(employee_id)
    remote_results = _call_search_policy_documents(
        "remote work eligibility international remote work approval duration location",
        top_k=3,
    )
    security_results = _call_search_policy_documents(
        "data security remote work requirements",
        top_k=2,
    )
    results = _merge_results(remote_results + security_results)
    answer = _remote_work_answer(employee_id, profile, results)

    return {
        "answer": answer,
        "citations": _citations_from_results(results),
        "tool_trace": [
            _trace_employee_profile(employee_id, profile),
            _trace_policy_search(
                "remote work eligibility international remote work approval duration location",
                3,
                remote_results,
            ),
            _trace_policy_search("data security remote work requirements", 2, security_results),
        ],
    }


def _handle_benefits_workflow(employee_id: str | None) -> dict:
    if not employee_id:
        return _missing_employee_id_response("benefits")

    profile = _call_lookup_employee_profile(employee_id)
    benefits = _call_lookup_benefits_status(employee_id)
    results = _call_search_policy_documents(
        "benefits eligibility medical dental vision retirement",
        top_k=3,
    )
    answer = _benefits_answer(employee_id, profile, benefits, results)

    return {
        "answer": answer,
        "citations": _citations_from_results(results),
        "tool_trace": [
            _trace_employee_profile(employee_id, profile),
            _trace_benefits_status(employee_id, benefits),
            _trace_policy_search(
                "benefits eligibility medical dental vision retirement",
                3,
                results,
            ),
        ],
    }


def _handle_expense_workflow(message: str) -> dict:
    query = f"{message} expense reimbursement approval equipment home office travel"
    results = _call_search_policy_documents(query, top_k=3)
    tool_trace = [_trace_policy_search(query, 3, results)]

    if "travel" in message.lower():
        travel_query = "travel policy approval director business travel expenses"
        travel_results = _call_search_policy_documents(travel_query, top_k=2)
        results = _merge_results(results + travel_results)
        tool_trace.append(_trace_policy_search(travel_query, 2, travel_results))

    return {
        "answer": _policy_answer(results),
        "citations": _citations_from_results(results),
        "tool_trace": tool_trace,
    }


def _extract_employee_id(message: str) -> str | None:
    match = EMPLOYEE_ID_PATTERN.search(message)

    if not match:
        return None

    return match.group(0).upper()


def _extract_requested_days(message: str) -> int | None:
    text = message.lower()
    digit_match = re.search(r"\b(\d+)\s+(?:business\s+)?days?\b", text)

    if digit_match:
        return int(digit_match.group(1))

    for word, value in NUMBER_WORDS.items():
        if re.search(rf"\b{word}\s+(?:business\s+)?days?\b", text):
            return value

    return None


def _wants_draft(message: str) -> bool:
    return _has_any(message.lower(), ["draft", "message", "email"])


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _has_word(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


def _missing_employee_id_response(workflow_name: str) -> dict:
    return {
        "answer": (
            f"I can help with that {workflow_name} workflow. "
            "Please provide an employee ID like E1001 so I can look up the synthetic "
            "employee record."
        ),
        "citations": [],
        "tool_trace": [
            {
                "tool": "none",
                "arguments": {"workflow": workflow_name},
                "result_summary": "Employee ID is required before calling MCP-exposed tools.",
            }
        ],
    }


def _policy_answer(results: list[dict]) -> str:
    if not results:
        return (
            "I could not find a matching Acme Horizon policy section. "
            "Try asking about PTO, remote work, benefits, expenses, onboarding, "
            "equipment, conduct, or travel."
        )

    guidance = "\n\n".join(
        f"- {result['title']} / {result['section']}: {result['snippet']}"
        for result in results
    )
    return f"I found the following relevant policy guidance:\n\n{guidance}"


def _pto_answer(
    employee_id: str,
    profile: dict,
    pto_balance: dict,
    results: list[dict],
    requested_days: int | None = None,
    draft_email: dict | None = None,
) -> str:
    lines = ["Summary decision"]
    employee = profile.get("employee")
    balance = pto_balance.get("pto_balance")

    if balance and requested_days and requested_days > balance["remaining_pto_days"]:
        lines.append(
            f"The request is not fully supported by the current PTO balance: "
            f"{requested_days} days requested, but only "
            f"{balance['remaining_pto_days']} days remaining. It may require unpaid "
            "leave, a date adjustment, or a manager/HR exception if policy allows."
        )
    elif balance and requested_days:
        lines.append(
            f"The request appears supportable from the current balance: "
            f"{requested_days} days requested and {balance['remaining_pto_days']} days remain."
        )
    elif balance:
        lines.append(
            f"The employee has {balance['remaining_pto_days']} days of PTO remaining."
        )
    else:
        lines.append("I could not confirm the employee's PTO balance from mock data.")

    lines.append("Employee context")
    if employee:
        lines.append(
            f"{employee['name']} is a {employee['employment_type']} "
            f"{employee['role']} in the {employee['office']} office."
        )
    else:
        lines.append(profile["message"])

    lines.append("PTO balance")
    if balance:
        lines.append(
            "\n".join(
                [
                f"- Annual PTO allowance: {balance['annual_pto_allowance_days']} days",
                f"- PTO used: {balance['used_pto_days']} days",
                f"- PTO remaining: {balance['remaining_pto_days']} days",
                f"- Requested PTO: {requested_days if requested_days else 'not specified'} days",
                ]
            )
        )
    else:
        lines.append(pto_balance["message"])

    lines.append("Policy basis")
    if results:
        lines.extend(_result_bullets(results))
    else:
        lines.append("No matching PTO policy snippets were found.")

    if draft_email and draft_email.get("status") == "draft_created":
        lines.append("Draft manager message")
        lines.append(f"Subject: {draft_email['subject']}\n\n{draft_email['body']}")

    lines.append("Next steps")
    lines.append(
        "Confirm the requested dates with the manager, adjust the request if the "
        "balance is short, and involve HR if an unpaid leave option or exception is needed."
    )

    return "\n\n".join(lines)


def _remote_work_answer(employee_id: str, profile: dict, results: list[dict]) -> str:
    lines = ["Summary decision"]
    employee = profile.get("employee")

    lines.append(
        "The Canada remote-work request should not be treated as automatically approved. "
        "Because it is international remote work and lasts six weeks, it requires written "
        "approval before work begins."
    )

    lines.append("Employee context")
    if employee:
        lines.append(
            f"{employee['name']} has this work arrangement: "
            f"{employee['work_arrangement']}. Role: {employee['employment_type']} "
            f"{employee['role']} based in the {employee['office']} office."
        )
    else:
        lines.append(profile["message"])

    lines.append("Policy basis")
    if results:
        lines.extend(_result_bullets(results))
    else:
        lines.append("No matching remote work policy snippets were found.")

    lines.append("Required approvals or next steps")
    lines.append(
        "Get manager approval first, then route the request to HR, Legal, Security, "
        "and Payroll at least 30 days before the Canada work period if possible."
    )

    lines.append("Security or location concerns")
    lines.append(
        "The employee should use approved company devices, VPN where required, trusted "
        "networks, and approved systems for company data. Payroll, tax, immigration, and "
        "data security review may be needed because the work location is outside the U.S."
    )

    return "\n\n".join(lines)


def _benefits_answer(
    employee_id: str,
    profile: dict,
    benefits: dict,
    results: list[dict],
) -> str:
    lines = [f"Here is the synthetic benefits workflow summary for {employee_id}."]
    employee = profile.get("employee")
    benefits_record = benefits.get("benefits")

    if employee:
        lines.append(
            f"{employee['name']} has {employee['benefits_eligibility']} benefits eligibility."
        )
    else:
        lines.append(profile["message"])

    if benefits_record:
        lines.append(
            "Current mock enrollment status: "
            f"medical={benefits_record['medical']}, dental={benefits_record['dental']}, "
            f"vision={benefits_record['vision']}, retirement={benefits_record['retirement_plan']}."
        )
    else:
        lines.append(benefits["message"])

    if results:
        lines.append("Relevant benefits policy guidance:")
        lines.extend(_result_bullets(results))

    return "\n\n".join(lines)


def _result_bullets(results: list[dict]) -> list[str]:
    return [
        f"- {result['title']} / {result['section']}: {result['snippet']}"
        for result in results
    ]


def _citations_from_results(results: list[dict]) -> list[dict]:
    citations = []
    seen = set()

    for result in results:
        key = (result["title"], result["section"], result["source"], result["snippet"])
        if key in seen:
            continue

        seen.add(key)
        citations.append(
            {
                "title": result["title"],
                "section": result["section"],
                "source": result["source"],
                "snippet": result["snippet"],
            }
        )

    return citations


def _merge_results(results: list[dict]) -> list[dict]:
    merged = []
    seen = set()

    for result in results:
        key = (result["source"], result["section"])
        if key in seen:
            continue

        seen.add(key)
        merged.append(result)

    return merged


def _call_search_policy_documents(query: str, top_k: int) -> list[dict]:
    response = call_tool(
        "search_policy_documents",
        {"query": query, "top_k": top_k},
    )
    return response.get("result", []) if response["status"] == "ok" else []


def _call_lookup_employee_profile(employee_id: str) -> dict:
    response = call_tool("lookup_employee_profile", {"employee_id": employee_id})
    return response.get("result", _tool_error_response(response))


def _call_check_pto_balance(employee_id: str) -> dict:
    response = call_tool("check_pto_balance", {"employee_id": employee_id})
    return response.get("result", _tool_error_response(response))


def _call_lookup_benefits_status(employee_id: str) -> dict:
    response = call_tool("lookup_benefits_status", {"employee_id": employee_id})
    return response.get("result", _tool_error_response(response))


def _call_draft_hr_email(
    employee_id: str,
    purpose: str,
    recipient_type: str,
) -> dict:
    response = call_tool(
        "draft_hr_email",
        {
            "employee_id": employee_id,
            "purpose": purpose,
            "recipient_type": recipient_type,
        },
    )
    return response.get("result", _tool_error_response(response))


def _tool_error_response(response: dict) -> dict:
    return {
        "status": "error",
        "message": response.get("message", "Tool call failed."),
    }


def _trace_policy_search(query: str, top_k: int, results: list[dict]) -> dict:
    return {
        "tool": "search_policy_documents",
        "arguments": {"query": query, "top_k": top_k},
        "result_summary": f"Retrieved {len(results)} policy chunks.",
    }


def _trace_employee_profile(employee_id: str, result: dict) -> dict:
    return {
        "tool": "lookup_employee_profile",
        "arguments": {"employee_id": employee_id},
        "result_summary": _employee_summary(result),
    }


def _trace_pto_balance(employee_id: str, result: dict) -> dict:
    balance = result.get("pto_balance")
    summary = (
        f"Found PTO balance with {balance['remaining_pto_days']} days remaining."
        if balance
        else result["message"]
    )
    return {
        "tool": "check_pto_balance",
        "arguments": {"employee_id": employee_id},
        "result_summary": summary,
    }


def _trace_benefits_status(employee_id: str, result: dict) -> dict:
    benefits = result.get("benefits")
    summary = (
        f"Found benefits status: {benefits['eligibility_status']}, "
        f"{benefits['enrollment_status']}."
        if benefits
        else result["message"]
    )
    return {
        "tool": "lookup_benefits_status",
        "arguments": {"employee_id": employee_id},
        "result_summary": summary,
    }


def _trace_draft_hr_email(employee_id: str, result: dict) -> dict:
    summary = (
        f"Drafted unsent email subject: {result['subject']}"
        if result.get("status") == "draft_created"
        else result["message"]
    )
    return {
        "tool": "draft_hr_email",
        "arguments": {
            "employee_id": employee_id,
            "purpose": "PTO request guidance",
            "recipient_type": "manager",
        },
        "result_summary": summary,
    }


def _employee_summary(result: dict[str, Any]) -> str:
    employee = result.get("employee")

    if not employee:
        return result["message"]

    return (
        f"Found employee {employee['name']}, {employee['employment_type']} "
        f"{employee['role']}, {employee['office']} office."
    )
