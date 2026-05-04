"""Session 6 -- optional two-agent triage: research (tools + RAG) then synthesis (JSON only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from src.json_repair import ai_content_str, parse_triage_json, repair_triage_json
from src.redaction import redact_incident
from src.schema import TriageOutput
from src.session1 import _final_triage_assistant_text, _repo_root, _system_prompt, get_llm
from src.tools_rag import TOOLS_SESSION3


def _trace_from_messages(messages: list[Any]) -> list[dict[str, Any]]:
    trace: list[dict[str, Any]] = []
    for m in messages:
        d: dict[str, Any] = {"type": m.__class__.__name__}
        if isinstance(m, AIMessage):
            d["tool_calls"] = getattr(m, "tool_calls", None)
            body = ai_content_str(m)
            d["content_preview"] = body[:500] if body else ""
        trace.append(d)
    return trace


def run_research_phase(incident: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    """Phase 1: ReAct agent with Session 3 tools; final message contains ### Research summary."""
    llm = get_llm()
    prompt = _system_prompt("session6_research.txt")
    graph = create_react_agent(llm, TOOLS_SESSION3, prompt=prompt)
    user = json.dumps(incident, indent=2)
    state = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        f"Incident JSON:\n{user}\n\n"
                        "Use tools to investigate. When finished, your FINAL assistant message must include "
                        "a section starting with exactly:\n\n### Research summary\n\n"
                        "Then bullets. Do NOT output the triage JSON schema."
                    )
                )
            ]
        }
    )
    messages = list(state.get("messages", []))
    text = _final_triage_assistant_text(messages)
    return text, _trace_from_messages(messages)


def run_synthesis_phase(incident: dict[str, Any], research_notes: str) -> tuple[TriageOutput, str]:
    """Phase 2: single LLM call; output must be TriageOutput JSON only."""
    llm = get_llm()
    syn = _system_prompt("session6_synthesis.txt")
    body = (
        f"{syn}\n\n---\nIncident JSON:\n{json.dumps(incident, indent=2)}\n\n"
        f"---\nResearch notes:\n{research_notes}\n"
    )
    out = llm.invoke([HumanMessage(content=body)])
    if not isinstance(out, AIMessage):
        raise RuntimeError("Synthesis returned no AIMessage")
    raw = ai_content_str(out)
    fail_path = _repo_root() / "triage_parse_failure.txt"
    try:
        triage = parse_triage_json(raw)
    except (json.JSONDecodeError, ValueError) as e:
        triage = repair_triage_json(llm, raw, str(e), failure_path=fail_path)
    return triage, raw


def run_multi_agent_triage(
    incident: dict[str, Any],
    *,
    redact: bool = True,
) -> tuple[TriageOutput, dict[str, Any]]:
    """
    Research agent (tools + RAG) -> synthesis agent (strict JSON).

    Returns ``(triage, trace)`` where ``trace`` includes research message previews and
    synthesis text preview.
    """
    payload = redact_incident(incident) if redact else incident
    research_text, research_trace = run_research_phase(payload)
    triage, synthesis_raw = run_synthesis_phase(payload, research_text)
    trace = {
        "session": 6,
        "research_message_trace": research_trace,
        "research_final_preview": research_text[:4000],
        "synthesis_raw_preview": synthesis_raw[:2000],
    }
    return triage, trace


def triage_session6_from_incident_path(path: str | Path) -> tuple[TriageOutput, dict[str, Any]]:
    p = Path(path)
    incident = json.loads(p.read_text(encoding="utf-8"))
    return run_multi_agent_triage(incident, redact=True)
