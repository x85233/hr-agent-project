import importlib
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVAL_QUESTIONS_PATH = PROJECT_ROOT / "evaluation" / "eval_questions.json"


def test_eval_questions_file_exists() -> None:
    assert EVAL_QUESTIONS_PATH.exists()


def test_eval_questions_has_at_least_twenty_items() -> None:
    questions = json.loads(EVAL_QUESTIONS_PATH.read_text(encoding="utf-8"))

    assert len(questions) >= 20


def test_run_eval_can_be_imported() -> None:
    module = importlib.import_module("evaluation.run_eval")

    assert hasattr(module, "main")


def test_at_least_one_eval_item_expects_policy_search() -> None:
    questions = json.loads(EVAL_QUESTIONS_PATH.read_text(encoding="utf-8"))

    assert any(
        "search_policy_documents" in item["expected_tools"]
        for item in questions
    )


def test_eval_set_includes_out_of_scope_request() -> None:
    questions = json.loads(EVAL_QUESTIONS_PATH.read_text(encoding="utf-8"))

    assert any(item["category"] == "out_of_scope_request" for item in questions)


def test_eval_set_includes_action_safety_item() -> None:
    questions = json.loads(EVAL_QUESTIONS_PATH.read_text(encoding="utf-8"))

    assert any(item["category"] == "action_safety" for item in questions)
