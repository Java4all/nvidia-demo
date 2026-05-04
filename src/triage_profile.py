"""Map session number (1–3) to prompt file, redaction, and tool set."""

from __future__ import annotations

from typing import Any

from src.schema import TriageOutput
from src.session1 import run_triage
from src.tools_log import TOOLS as TOOLS_S1
from src.tools_rag import TOOLS_SESSION3


def run_triage_for_session(
    incident: dict[str, Any],
    session: int = 3,
) -> tuple[TriageOutput, list[dict[str, Any]]]:
    """
    Session **1** — baseline tools, session1 prompt, no redaction.
    Session **2** — same tools, session2 prompt, redaction.
    Session **3** — RAG tools, session3 prompt, redaction (default for CLI/eval).
    """
    if session == 1:
        return run_triage(incident, prompt_file="session1_system.txt", redact=False, tools=TOOLS_S1)
    if session == 2:
        return run_triage(incident, prompt_file="session2_system.txt", redact=True, tools=TOOLS_S1)
    if session == 3:
        return run_triage(
            incident,
            prompt_file="session3_system.txt",
            redact=True,
            tools=TOOLS_SESSION3,
        )
    raise ValueError(f"session must be 1, 2, or 3, got {session}")
