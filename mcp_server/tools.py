import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from rag.ingest import load_policy_chunks
from rag.retriever import search_policies


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MOCK_DATA_DIR = PROJECT_ROOT / "mock_data"


def search_policy_documents(query: str, top_k: int = 3) -> list[dict]:
    return search_policies(query=query, top_k=top_k)


def get_policy_section(source: str, section: str) -> dict:
    for chunk in load_policy_chunks():
        if (
            chunk["source"].lower() == source.lower()
            and chunk["section"].lower() == section.lower()
        ):
            return {
                "status": "found",
                "title": chunk["title"],
                "section": chunk["section"],
                "source": chunk["source"],
                "snippet": chunk["snippet"],
                "text": chunk["text"],
            }

    return {
        "status": "not_found",
        "source": source,
        "section": section,
        "message": "No matching policy section was found.",
    }


def lookup_employee_profile(employee_id: str) -> dict:
    employee = _find_by_employee_id("employees.json", employee_id)

    if employee:
        return {"status": "found", "employee": employee}

    return _not_found("employee", employee_id)


def check_pto_balance(employee_id: str) -> dict:
    pto_balance = _find_by_employee_id("pto_balances.json", employee_id)

    if pto_balance:
        return {"status": "found", "pto_balance": pto_balance}

    return _not_found("pto_balance", employee_id)


def lookup_benefits_status(employee_id: str) -> dict:
    benefits = _find_by_employee_id("benefits.json", employee_id)

    if benefits:
        return {"status": "found", "benefits": benefits}

    return _not_found("benefits", employee_id)


def create_mock_hr_ticket(employee_id: str, issue_type: str, summary: str) -> dict:
    tickets_path = MOCK_DATA_DIR / "tickets.json"
    tickets = _read_json_file(tickets_path)
    ticket_id = f"MOCK-{uuid4().hex[:8].upper()}"
    ticket = {
        "ticket_id": ticket_id,
        "employee_id": employee_id,
        "category": issue_type,
        "subject": f"Mock HR ticket: {issue_type}",
        "status": "mock_created",
        "created_at": datetime.now(UTC).isoformat(),
        "summary": summary,
        "synthetic": True,
    }

    tickets.append(ticket)
    tickets_path.write_text(json.dumps(tickets, indent=2), encoding="utf-8")

    return {
        "ticket_id": ticket_id,
        "status": "mock_created",
        "summary": summary,
        "message": "Synthetic mock ticket created. No real HR workflow was triggered.",
    }


def draft_hr_email(
    employee_id: str,
    purpose: str,
    recipient_type: str = "manager",
) -> dict:
    profile_response = lookup_employee_profile(employee_id)

    if profile_response["status"] != "found":
        return profile_response

    employee = profile_response["employee"]
    subject = f"Draft: {purpose} for {employee['name']}"
    body = (
        f"Hello {recipient_type},\n\n"
        f"This is a draft HR email regarding {purpose} for {employee['name']} "
        f"({employee_id}), a {employee['employment_type']} {employee['role']} "
        f"based in the {employee['office']} office.\n\n"
        "Please review the relevant Acme Horizon policy guidance before taking action.\n\n"
        "This is a synthetic draft only and has not been sent."
    )

    return {
        "status": "draft_created",
        "employee_id": employee_id,
        "recipient_type": recipient_type,
        "subject": subject,
        "body": body,
        "sent": False,
    }


def _find_by_employee_id(file_name: str, employee_id: str) -> dict | None:
    records = _read_json_file(MOCK_DATA_DIR / file_name)

    for record in records:
        if record.get("employee_id") == employee_id:
            return record

    return None


def _read_json_file(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _not_found(record_type: str, employee_id: str) -> dict:
    return {
        "status": "not_found",
        "employee_id": employee_id,
        "message": f"No {record_type} record found for employee_id {employee_id}.",
    }
