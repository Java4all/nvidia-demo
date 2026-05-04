"""Tests for Session 4 incident builder."""

from __future__ import annotations

from src.cli_incident import build_incident


def test_build_minimal() -> None:
    inc = build_incident("CPU spike", "line1\nline2")
    assert inc["alert"]["title"] == "CPU spike"
    assert inc["log_excerpts"] == ["line1", "line2"]
    assert inc["context"]["service"] == "unknown"


def test_build_empty_logs_placeholder() -> None:
    inc = build_incident("Disk full", None)
    assert len(inc["log_excerpts"]) == 1
    assert "no log" in inc["log_excerpts"][0].lower()
