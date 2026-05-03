"""Session 1 — tool-calling agent + strict JSON triage (OpenAI-compatible NIM/Ollama)."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from src.schema import TriageOutput
from src.tools_log import TOOLS


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_dotenv() -> None:
    load_dotenv(_repo_root() / ".env", override=False)


def _system_prompt() -> str:
    path = _repo_root() / "src" / "prompts" / "session1_system.txt"
    return path.read_text(encoding="utf-8").strip()


def _ai_content_str(msg: AIMessage) -> str:
    c = msg.content
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts: list[str] = []
        for block in c:
            if isinstance(block, dict):
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    parts.append(block["text"])
                elif isinstance(block.get("text"), str):
                    parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return ""


_load_dotenv()


def _llm() -> ChatOpenAI:
    raw = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:8000/v1").rstrip("/")
    base = raw if raw.endswith("/v1") else f"{raw}/v1"
    key = os.environ.get("OPENAI_API_KEY", "not-used")
    model = os.environ.get("OPENAI_MODEL")
    if not model:
        raise RuntimeError(
            "Set OPENAI_MODEL to the model id your server exposes "
            "(from GET {OPENAI_BASE_URL}/models when base ends with /v1)."
        )
    return ChatOpenAI(
        model=model,
        api_key=key,
        base_url=base,
        temperature=0,
        timeout=300,
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
    if not isinstance(out, AIMessage):
        raise ValueError("repair pass returned no AIMessage")
    body = _ai_content_str(out)
    if not body.strip():
        raise ValueError("repair pass returned empty content")
    return _parse_triage_json(body)


def _last_non_empty_assistant_text(messages: list[Any]) -> str:
    for m in reversed(messages):
        if isinstance(m, AIMessage):
            t = _ai_content_str(m).strip()
            if t:
                return _ai_content_str(m)
    raise RuntimeError("Agent returned no assistant message with text content")


def run_triage(incident: dict[str, Any]) -> tuple[TriageOutput, list[dict[str, Any]]]:
    """
    Run the Session 1 agent. Returns (triage, lightweight message trace for debugging).
    """
    llm = _llm()
    graph = create_react_agent(llm, TOOLS, prompt=_system_prompt())

    user = json.dumps(incident, indent=2)
    state = graph.invoke(
        {"messages": [HumanMessage(content=f"Incident JSON:\n{user}\n\nProduce the triage JSON.")]}
    )

    messages = list(state.get("messages", []))
    last_ai = _last_non_empty_assistant_text(messages)

    trace: list[dict[str, Any]] = []
    for m in messages:
        d: dict[str, Any] = {"type": m.__class__.__name__}
        if isinstance(m, AIMessage):
            d["tool_calls"] = getattr(m, "tool_calls", None)
            body = _ai_content_str(m)
            d["content_preview"] = body[:500] if body else ""
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
