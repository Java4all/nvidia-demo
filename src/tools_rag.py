"""Session 3 tools: log helpers + RAG over ``data/docs`` (replaces stub playbook)."""

from __future__ import annotations

from langchain_core.tools import tool

from src.rag_runbooks import RunbookIndex
from src.tools_log import classify_severity_keywords, extract_timestamps_and_ids

_repo_index: RunbookIndex | None = None


def _index() -> RunbookIndex:
    global _repo_index
    if _repo_index is None:
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        _repo_index = RunbookIndex.from_docs_dir(root / "data" / "docs")
    return _repo_index


@tool
def lookup_runbook_rag(alert_title: str, search_hint: str = "") -> str:
    """Search internal runbook markdown (data/docs). Use alert title and optional hint (service, error, region). Returns top excerpts with source paths."""
    q = f"{alert_title} {search_hint}".strip()
    rows = _index().retrieve(q, top_k=4)
    if not rows:
        return "No runbook chunks matched. Try a broader search_hint (service name, error token)."
    lines: list[str] = []
    for rel, chunk, _score in rows:
        lines.append(f"## {rel}\n{chunk}\n")
    return "\n".join(lines).strip()


TOOLS_SESSION3 = [
    extract_timestamps_and_ids,
    classify_severity_keywords,
    lookup_runbook_rag,
]
