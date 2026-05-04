"""Unit tests for Session 5 eval expectations (no LLM)."""

from __future__ import annotations

from pathlib import Path

from src.eval_harness import check_expectations, load_eval_cases, resolve_incident
from src.schema import Escalate, LikelyCause, Reference, Signals, TriageOutput


def _sample_triage() -> TriageOutput:
    return TriageOutput(
        summary="checkout-api errors during payment timeouts",
        signals=Signals(errors=["e"], warnings=[], notable_ids=[]),
        likely_causes=[LikelyCause(cause="gw", confidence="high", evidence="logs")],
        next_steps=["step1", "step2"],
        escalate=Escalate(required=True, reason="budget"),
        references=[Reference(source="payments_dependency.md", excerpt="x")],
    )


def test_check_expectations_pass() -> None:
    t = _sample_triage()
    assert check_expectations(t, {"summary_contains": ["checkout"], "escalate_required": True}) == []


def test_check_expectations_summary_fail() -> None:
    t = _sample_triage()
    bad = check_expectations(t, {"summary_contains": ["nomatch"]})
    assert bad


def test_resolve_incident_path(tmp_path: Path) -> None:
    repo = tmp_path
    (repo / "sub").mkdir()
    inc = {"alert": {"title": "t"}, "context": {}, "log_excerpts": []}
    (repo / "sub" / "i.json").write_text(__import__("json").dumps(inc), encoding="utf-8")
    got = resolve_incident({"incident_path": "sub/i.json"}, repo_root=repo)
    assert got["alert"]["title"] == "t"


def test_load_eval_cases_skips_comments(tmp_path: Path) -> None:
    p = tmp_path / "c.jsonl"
    p.write_text('# comment\n{"id": "a", "incident": {"alert":{"title":"x","severity":"P1","source":"s","fired_at":"t"},"context":{"environment":"e","region":"r","service":"s"},"log_excerpts":[]}, "expect": {}}\n', encoding="utf-8")
    cases = load_eval_cases(p)
    assert len(cases) == 1
    assert cases[0]["id"] == "a"
