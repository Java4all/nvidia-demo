"""Tests for Session 3 runbook RAG index."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.rag_runbooks import RunbookIndex


@pytest.fixture
def docs_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "docs"


def test_index_loads_markdown(docs_dir: Path) -> None:
    idx = RunbookIndex.from_docs_dir(docs_dir)
    assert len(idx._chunks) >= 3


def test_retrieve_prefers_payments_for_checkout(docs_dir: Path) -> None:
    idx = RunbookIndex.from_docs_dir(docs_dir)
    hits = idx.retrieve("checkout payment timeout payments-gw", top_k=3)
    assert hits
    paths = [h[0] for h in hits]
    assert any("payments" in p for p in paths)
