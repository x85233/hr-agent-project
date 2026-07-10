import re

from rag.ingest import load_policy_chunks


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "do",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "with",
}


def search_policies(query: str, top_k: int = 3) -> list[dict]:
    query_terms = _tokenize(query)

    if not query_terms:
        return []

    scored_chunks = []
    for chunk in load_policy_chunks():
        score = _score_chunk(query_terms, chunk)

        if score == 0:
            continue

        scored_chunks.append((_format_result(chunk, score), score))

    scored_chunks.sort(
        key=lambda item: (
            item[1],
            item[0]["title"].lower(),
            item[0]["section"].lower(),
        ),
        reverse=True,
    )

    return [item[0] for item in scored_chunks[:top_k]]


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if word not in STOPWORDS and len(word) > 1}


def _score_chunk(query_terms: set[str], chunk: dict) -> float:
    title_terms = _tokenize(chunk["title"])
    section_terms = _tokenize(chunk["section"])
    source_terms = _tokenize(chunk["source"].replace("_", " "))
    text_terms = _tokenize(chunk["text"])

    weighted_matches = (
        3 * len(query_terms.intersection(title_terms))
        + 2 * len(query_terms.intersection(source_terms))
        + 1.5 * len(query_terms.intersection(section_terms))
        + len(query_terms.intersection(text_terms))
    )

    return weighted_matches / len(query_terms)


def _format_result(chunk: dict, score: float) -> dict:
    return {
        "title": chunk["title"],
        "section": chunk["section"],
        "source": chunk["source"],
        "snippet": chunk["snippet"],
        "score": round(score, 3),
    }
