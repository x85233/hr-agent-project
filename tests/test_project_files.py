import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_policy_folder_exists_with_markdown_files() -> None:
    policies_dir = PROJECT_ROOT / "policies"

    assert policies_dir.exists()
    assert len(list(policies_dir.glob("*.md"))) >= 8


def test_mock_data_files_exist() -> None:
    mock_data_dir = PROJECT_ROOT / "mock_data"

    assert (mock_data_dir / "employees.json").exists()
    assert (mock_data_dir / "pto_balances.json").exists()
    assert (mock_data_dir / "benefits.json").exists()


def test_employee_data_includes_e1001() -> None:
    employees_path = PROJECT_ROOT / "mock_data" / "employees.json"

    employees = json.loads(employees_path.read_text(encoding="utf-8"))
    employee_ids = {employee["employee_id"] for employee in employees}

    assert "E1001" in employee_ids
