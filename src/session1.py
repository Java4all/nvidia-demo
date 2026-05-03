"""Session 1 — tool-calling agent + strict JSON triage (OpenAI-compatible NIM/Ollama)."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from src.schema import TriageOutput
from src.tools_log import TOOLS

load_dotenv()

SYSTEM_PROMPT = """You are an SRE log triage copilot.

Rules:
- Use the provided tools when they help; combine tool facts with the incident JSON.
- Only cite facts supported by the incident or tool outputs; if unsure, say so in evidence with low confidence.
- Your FINAL reply must be ONE JSON object only (no markdown fences, no prose before or after) matching this shape:
  {
    "summary": string,
    "signals": { "errors": string[], "warnings": string[], "notable_ids": string[] },
    "likely_causes": [ { "cause": string, "confidence": "low"|"med"|"high", "evidence": string } ],
    "next_steps": string[],
    "escalate": { "required": boolean, "reason": string },
    "references": [ { "source": string, "excerpt": string } ]
  }
- references may be empty if stub_lookup_playbook is the only "doc" — then set source to "stub_lookup_playbook" and excerpt to a short quote from that tool output.
"""


def _llm() -> ChatOpenAI:
    raw = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:8000/v1").rstrip("/")
    base = raw if raw.endswith("/v1") else f"{raw}/v1"
    key = os.environ.get("OPENAI_API_KEY", "not-used")
    model = os.environ.get("OPENAI_MODEL")
    if not model:
        raise RuntimeError(
            "Set OPENAI_MODEL to the model id your server exposes "
            "(e.g. from GET .../v1/models on NIM or Ollama)."
        )
    return ChatOpenAI(
        model=model,
        api_key=key,
        base_url=base,
        temperature=0,
        timeout=120,
    )


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    m = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text


def _parse_triage_json(text: str) -> TriageOutput:
    cleaned = _strip_json_fence(text)
    data = json.loads(cleaned)
    return TriageOutput.model_validate(data)


def _repair_json(llm: ChatOpenAI, bad_text: str, err: str) -> TriageOutput:
    msg = (
        "The following text was not valid JSON for the triage schema.\n"
        f"Parse error: {err}\n\n"
        "Return ONLY a corrected JSON object, no fences, no commentary:\n\n"
        + bad_text[:12000]
    )
    out = llm.invoke([HumanMessage(content=msg)])
    if not isinstance(out, AIMessage) or not isinstance(out.content, str):
        raise ValueError("repair pass returned no text")
    return _parse_triage_json(out.content)


def run_triage(incident: dict[str, Any]) -> tuple[TriageOutput, list[dict[str, Any]]]:
    """
    Run the Session 1 agent. Returns (triage, lightweight message trace for debugging).
    """
    llm = _llm()
    graph = create_react_agent(llm, TOOLS, prompt=SYSTEM_PROMPT)

    user = json.dumps(incident, indent=2)
    state = graph.invoke({"messages": [HumanMessage(content=f"Incident JSON:\n{user}\n\nProduce the triage JSON.")]})

    messages = state.get("messages", [])
    last_ai: str | None = None
    for m in reversed(messages):
        if isinstance(m, AIMessage) and isinstance(m.content, str) and m.content.strip():
            last_ai = m.content
            break
    if not last_ai:
        raise RuntimeError("Agent returned no assistant text")

    trace = []
    for m in messages:
        d: dict[str, Any] = {"type": m.__class__.__name__}
        if isinstance(m, AIMessage):
            d["tool_calls"] = getattr(m, "tool_calls", None)
            if isinstance(m.content, str):
                d["content_preview"] = m.content[:500]
        trace.append(d)

    try:
        triage = _parse_triage_json(last_ai)
    except (json.JSONDecodeError, ValueError) as e:
        triage = _repair_json(llm, last_ai, str(e))

    return triage, trace


def triage_from_incident_path(path: str) -> tuple[TriageOutput, list[dict[str, Any]]]:
    with open(path, encoding="utf-8") as f:
        incident = json.load(f)
    return run_triage(incident)
