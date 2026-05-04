"""Session 1 — tool-calling agent + strict JSON triage (OpenAI-compatible NIM/Ollama)."""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Any, override

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from src.json_repair import ai_content_str, parse_triage_json, repair_triage_json
from src.redaction import redact_incident
from src.schema import TriageOutput
from src.tools_log import TOOLS


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_dotenv() -> None:
    load_dotenv(_repo_root() / ".env", override=False)


def _system_prompt(prompt_file: str = "session1_system.txt") -> str:
    path = _repo_root() / "src" / "prompts" / prompt_file
    return path.read_text(encoding="utf-8").strip()


_load_dotenv()


def _parallel_tool_calls_from_env() -> bool:
    """NIM/vLLM often allow only one tool call per assistant turn (no parallel batching)."""
    for key in ("SESSION1_PARALLEL_TOOL_CALLS", "OPENAI_PARALLEL_TOOL_CALLS"):
        v = os.environ.get(key, "").strip().lower()
        if v in ("1", "true", "yes", "on"):
            return True
        if v in ("0", "false", "no", "off"):
            return False
    return False


def _strip_tool_choice_from_env() -> bool:
    """vLLM/NIM reject OpenAI-style tool_choice='auto' unless the server enables it."""
    force = os.environ.get("SESSION1_FORCE_STRIP_TOOL_CHOICE", "").strip().lower()
    if force in ("1", "true", "yes", "on"):
        return True
    v = os.environ.get("OPENAI_STRIP_TOOL_CHOICE", "1").strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    return True


def _strip_tool_choice_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    out = dict(kwargs)
    out.pop("tool_choice", None)
    eb = out.get("extra_body")
    if isinstance(eb, Mapping):
        eb2 = dict(eb)
        eb2.pop("tool_choice", None)
        out["extra_body"] = eb2
    return out


_openai_create_patch_lock = threading.Lock()
_openai_orig_sync_create: Any = None
_openai_orig_async_create: Any = None


def _ensure_openai_completions_strip_tool_choice_patch() -> None:
    """Patch SDK ``create`` so NIM/vLLM never see ``tool_choice`` (LangChain may bypass LC hooks)."""
    global _openai_orig_sync_create, _openai_orig_async_create
    with _openai_create_patch_lock:
        if _openai_orig_sync_create is not None:
            return
        from openai.resources.chat.completions.completions import AsyncCompletions, Completions

        _openai_orig_sync_create = Completions.create

        def _sync_create(self: Any, *args: Any, **kwargs: Any) -> Any:
            if _strip_tool_choice_from_env():
                kwargs = _strip_tool_choice_kwargs(kwargs)
            return _openai_orig_sync_create(self, *args, **kwargs)

        Completions.create = _sync_create  # type: ignore[method-assign]

        _openai_orig_async_create = AsyncCompletions.create

        async def _async_create(self: Any, *args: Any, **kwargs: Any) -> Any:
            if _strip_tool_choice_from_env():
                kwargs = _strip_tool_choice_kwargs(kwargs)
            return await _openai_orig_async_create(self, *args, **kwargs)

        AsyncCompletions.create = _async_create  # type: ignore[method-assign]


class _ChatOpenAIStripToolChoice(ChatOpenAI):
    """Drop ``tool_choice`` from chat-completions payloads (NIM / vLLM compatibility)."""

    @override
    def _get_request_payload(  # type: ignore[override]
        self,
        input_: Any,
        *,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if _strip_tool_choice_from_env():
            kwargs = dict(kwargs)
            kwargs.pop("tool_choice", None)
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)
        if _strip_tool_choice_from_env():
            payload.pop("tool_choice", None)
        return payload


def _llm() -> ChatOpenAI:
    _ensure_openai_completions_strip_tool_choice_patch()
    raw = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:8000/v1").rstrip("/")
    base = raw if raw.endswith("/v1") else f"{raw}/v1"
    key = os.environ.get("OPENAI_API_KEY", "not-used")
    model = os.environ.get("OPENAI_MODEL")
    if not model:
        raise RuntimeError(
            "Set OPENAI_MODEL to the model id your server exposes "
            "(from GET {OPENAI_BASE_URL}/models when base ends with /v1)."
        )
    model_kwargs: dict[str, Any] = {"parallel_tool_calls": _parallel_tool_calls_from_env()}
    llm = _ChatOpenAIStripToolChoice(
        model=model,
        api_key=key,
        base_url=base,
        temperature=0,
        timeout=300,
        model_kwargs=model_kwargs,
    )
    if _strip_tool_choice_from_env() and llm.model_kwargs:
        llm.model_kwargs.pop("tool_choice", None)
    return llm


def _final_triage_assistant_text(messages: list[Any]) -> str:
    """
    Prefer the chronologically last assistant message with content.

    Scanning only for the last non-empty text can pick an earlier turn instead of
    the final triage JSON.
    """
    last_ai: AIMessage | None = None
    for m in messages:
        if isinstance(m, AIMessage):
            last_ai = m
    if last_ai is None:
        raise RuntimeError("Agent returned no AIMessage")
    body = ai_content_str(last_ai).strip()
    if body:
        return ai_content_str(last_ai)
    for m in reversed(messages):
        if isinstance(m, AIMessage):
            t = ai_content_str(m).strip()
            if t:
                return ai_content_str(m)
    raise RuntimeError("Agent returned no assistant message with text content")


def run_triage(
    incident: dict[str, Any],
    *,
    prompt_file: str = "session1_system.txt",
    redact: bool = False,
    tools: list | None = None,
) -> tuple[TriageOutput, list[dict[str, Any]]]:
    """
    Run the log triage agent. Session 2 uses ``prompt_file=session2_system.txt`` and
    ``redact=True`` (see ``scripts/run_session2.py``). Session 3 passes
    ``tools=TOOLS_SESSION3`` and ``prompt_file=session3_system.txt`` (see
    ``scripts/run_session3.py``).
    """
    payload = redact_incident(incident) if redact else incident

    llm = _llm()
    tool_list = tools if tools is not None else TOOLS
    graph = create_react_agent(llm, tool_list, prompt=_system_prompt(prompt_file))

    user = json.dumps(payload, indent=2)
    state = graph.invoke(
        {"messages": [HumanMessage(content=f"Incident JSON:\n{user}\n\nProduce the triage JSON.")]}
    )

    messages = list(state.get("messages", []))
    last_ai = _final_triage_assistant_text(messages)

    trace: list[dict[str, Any]] = []
    for m in messages:
        d: dict[str, Any] = {"type": m.__class__.__name__}
        if isinstance(m, AIMessage):
            d["tool_calls"] = getattr(m, "tool_calls", None)
            body = ai_content_str(m)
            d["content_preview"] = body[:500] if body else ""
        trace.append(d)

    fail_path = _repo_root() / "triage_parse_failure.txt"
    try:
        triage = parse_triage_json(last_ai)
    except (json.JSONDecodeError, ValueError) as e:
        triage = repair_triage_json(llm, last_ai, str(e), failure_path=fail_path)

    return triage, trace


def triage_from_incident_path(
    path: str,
    *,
    prompt_file: str = "session1_system.txt",
    redact: bool = False,
    tools: list | None = None,
) -> tuple[TriageOutput, list[dict[str, Any]]]:
    with open(path, encoding="utf-8") as f:
        incident = json.load(f)
    return run_triage(incident, prompt_file=prompt_file, redact=redact, tools=tools)
