from fastapi.testclient import TestClient

from app.main import app
from rag.ingest import load_policy_chunks
from rag.retriever import search_policies


client = TestClient(app)


def test_load_policy_chunks_returns_chunks_from_at_least_eight_files() -> None:
    chunks = load_policy_chunks()
    source_files = {chunk["source"] for chunk in chunks}

    assert len(source_files) >= 8
    assert chunks[0]["title"]
    assert chunks[0]["section"]
    assert chunks[0]["snippet"]


def test_search_policies_returns_pto_related_result() -> None:
    results = search_policies("PTO balance vacation time")

    assert results
    assert any("pto" in result["title"].lower() for result in results)


def test_search_policies_returns_remote_work_related_result() -> None:
    results = search_policies("remote work from another country")

    assert results
    assert any("remote work" in result["title"].lower() for result in results)


def test_chat_returns_real_policy_citations() -> None:
    response = client.post(
        "/chat",
        json={"message": "Can E1001 work remotely abroad?"},
    )

    data = response.json()
    citation = data["citations"][0]

    assert response.status_code == 200
    assert citation["title"]
    assert citation["section"]
    assert citation["source"]
    assert citation["snippet"]
    assert any(
        entry["tool"] == "search_policy_documents"
        for entry in data["tool_trace"]
    )
