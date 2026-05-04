"""
Live LLM tests for Session 6 (optional).

These call your configured endpoint (.env: OPENAI_BASE_URL, OPENAI_MODEL, etc.).
Skip by default so CI / offline runs stay fast.

Enable::

  set RUN_LIVE_LLM=1
  python -m pytest tests/test_session6_live.py -v

Linux/macOS::

  export RUN_LIVE_LLM=1
  python -m pytest tests/test_session6_live.py -v

Requires: same runtime as ``python scripts/run_session6.py`` (NIM reachable, GPU optional).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _live_enabled() -> bool:
    return os.environ.get("RUN_LIVE_LLM", "").strip().lower() in ("1", "true", "yes", "on")


pytestmark = pytest.mark.skipif(
    not _live_enabled(),
    reason="Set RUN_LIVE_LLM=1 to run live Session 6 tests (needs .env + NIM/Ollama)",
)


def test_session6_multi_agent_incident_01() -> None:
    """End-to-end: research phase + synthesis -> TriageOutput."""
    from src.session6 import triage_session6_from_incident_path

    triage, trace = triage_session6_from_incident_path(ROOT / "samples" / "incident_01.json")
    assert triage.summary.strip()
    assert isinstance(trace, dict)
    assert trace.get("session") == 6
    assert "research_message_trace" in trace
    assert triage.escalate.required is not None
