from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POLICIES_DIR = PROJECT_ROOT / "policies"


def load_policy_chunks() -> list[dict]:
    chunks: list[dict] = []

    for policy_path in sorted(POLICIES_DIR.glob("*.md")):
        chunks.extend(_parse_policy_file(policy_path))

    return chunks


def _parse_policy_file(policy_path: Path) -> list[dict]:
    lines = policy_path.read_text(encoding="utf-8").splitlines()
    policy_title = policy_path.stem.replace("_", " ").title()
    current_section = "Overview"
    current_lines: list[str] = []
    chunks: list[dict] = []

    for line in lines:
        if line.startswith("# "):
            policy_title = line.removeprefix("# ").strip()
            continue

        if line.startswith("## "):
            _add_chunk(
                chunks=chunks,
                source=policy_path.name,
                title=policy_title,
                section=current_section,
                lines=current_lines,
            )
            current_section = line.removeprefix("## ").strip()
            current_lines = []
            continue

        current_lines.append(line)

    _add_chunk(
        chunks=chunks,
        source=policy_path.name,
        title=policy_title,
        section=current_section,
        lines=current_lines,
    )

    return chunks


def _add_chunk(
    chunks: list[dict],
    source: str,
    title: str,
    section: str,
    lines: list[str],
) -> None:
    text = "\n".join(lines).strip()

    if not text:
        return

    chunks.append(
        {
            "source": source,
            "title": title,
            "section": section,
            "text": text,
            "snippet": _shorten(text),
        }
    )


def _shorten(text: str, max_length: int = 240) -> str:
    clean_text = " ".join(text.split())

    if len(clean_text) <= max_length:
        return clean_text

    return clean_text[: max_length - 3].rstrip() + "..."
