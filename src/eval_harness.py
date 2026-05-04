"""Load eval cases (JSONL) and check TriageOutput against optional expectations (Session 5)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.schema import TriageOutput


def load_eval_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        cases.append(json.loads(line))
    return cases


def resolve_incident(case: dict[str, Any], *, repo_root: Path) -> dict[str, Any]:
    """Build incident dict from ``incident`` inline JSON or ``incident_path`` relative to repo root."""
    if "incident" in case:
        return dict(case["incident"])
    if "incident_path" in case:
        p = repo_root / case["incident_path"]
        return json.loads(p.read_text(encoding="utf-8"))
    raise ValueError("case must contain 'incident' or 'incident_path'")


def check_expectations(triage: TriageOutput, expect: dict[str, Any] | None) -> list[str]:
    """
    Return a list of human-readable failures (empty list => pass).

    Supported keys in ``expect``:

    - ``summary_contains``: each string must appear in ``summary`` (case-insensitive).
    - ``escalate_required``: exact match on ``escalate.required``.
    - ``reference_sources_contain``: each string must appear in some ``references[].source``.
    - ``min_next_steps``, ``min_likely_causes``: minimum list lengths.
    - ``signals_errors_nonempty``: if true, ``signals.errors`` must be non-empty.
    """
    if not expect:
        return []

    bad: list[str] = []
    summary_lower = triage.summary.lower()

    for needle in expect.get("summary_contains") or []:
        if needle.lower() not in summary_lower:
            bad.append(f"summary missing substring {needle!r}")

    if "escalate_required" in expect:
        want = bool(expect["escalate_required"])
        if triage.escalate.required != want:
            bad.append(f"escalate.required: want {want}, got {triage.escalate.required}")

    for needle in expect.get("reference_sources_contain") or []:
        n = needle.lower()
        if not any(n in r.source.lower() for r in triage.references):
            bad.append(f"no reference.source contains {needle!r}")

    if (m := expect.get("min_next_steps")) is not None:
        if len(triage.next_steps) < int(m):
            bad.append(f"next_steps: need >= {m}, got {len(triage.next_steps)}")

    if (m := expect.get("min_likely_causes")) is not None:
        if len(triage.likely_causes) < int(m):
            bad.append(f"likely_causes: need >= {m}, got {len(triage.likely_causes)}")

    if expect.get("signals_errors_nonempty"):
        if not triage.signals.errors:
            bad.append("signals.errors is empty")

    return bad
