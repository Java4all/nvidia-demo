"""Session 1 — tool-calling agent + strict JSON triage (OpenAI-compatible NIM/Ollama)."""

from __future__ import annotations

import json
import os
import re
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Any, override

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
    # OpenAI defaults parallel_tool_calls=True; many NIM backends error with
    # "only supports single tool-calls at once" — default off, opt in via env.
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


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    m = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text


def _extract_first_json_object_str(text: str) -> str:
    """Parse out the first top-level `{ ... }` value (handles preamble / trailing prose)."""
    text = _strip_json_fence(text).strip()
    decoder = json.JSONDecoder()
    start_search = 0
    while True:
        i = text.find("{", start_search)
        if i == -1:
            break
        try:
            _, end = decoder.raw_decode(text[i:])
            return text[i : i + end]
        except json.JSONDecodeError:
            start_search = i + 1
            continue
    raise json.JSONDecodeError("No JSON object found in model output", text, 0)


def _relax_json_commas(s: str) -> str:
    """Strip trailing commas before } or ] (common invalid JSON from LLMs)."""
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r",(\s*)([}\]])", r"\1\2", s)
    return s


def _parse_triage_json(text: str) -> TriageOutput:
    cleaned = _strip_json_fence(text)
    blobs: list[str] = [cleaned, _relax_json_commas(cleaned)]
    try:
        ext = _extract_first_json_object_str(text)
        blobs.extend([ext, _relax_json_commas(ext)])
    except json.JSONDecodeError:
        pass

    seen: set[str] = set()
    last_err: BaseException | None = None
    for raw in blobs:
        if raw in seen:
            continue
        seen.add(raw)
        try:
            data = json.loads(raw)
            return TriageOutput.model_validate(data)
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            continue
    if last_err is not None:
        raise last_err
    raise json.JSONDecodeError("Could not parse triage JSON", cleaned, 0)


def _repair_json(llm: ChatOpenAI, bad_text: str, err: str) -> TriageOutput:
    schema_hint = (
        '{"summary":"...","signals":{"errors":[],"warnings":[],"notable_ids":[]},'
        '"likely_causes":[{"cause":"...","confidence":"low|med|high","evidence":"..."}],'
        '"next_steps":[],"escalate":{"required":false,"reason":"..."},"references":[]}'
    )
    attempts = (
        (
            "The following text was not valid JSON for the triage schema.\n"
            f"Parse error: {err}\n\n"
            "Return ONLY a corrected JSON object, no markdown fences, no commentary:\n\n"
            + bad_text[:12000]
        ),
        (
            "Return ONLY one JSON object (no markdown, no text before or after). "
            "Keys: summary, signals, likely_causes, next_steps, escalate, references. "
            f"Shape example (structure only): {schema_hint}\n\nFix or rebuild from:\n\n"
            + bad_text[:12000]
        ),
    )
    last_inner: BaseException | None = None
    for msg in attempts:
        out = llm.invoke([HumanMessage(content=msg)])
        if not isinstance(out, AIMessage):
            raise ValueError("repair pass returned no AIMessage")
        body = _ai_content_str(out)
        if not body.strip():
            continue
        try:
            return _parse_triage_json(body)
        except (json.JSONDecodeError, ValueError) as e2:
            last_inner = e2
            continue
    fail_path = _repo_root() / "session1_parse_failure.txt"
    try:
        fail_path.write_text(
            f"# Last error: {err}\n# Repair errors: {last_inner!r}\n\n--- assistant text ---\n{bad_text[:50000]}",
            encoding="utf-8",
        )
    except OSError:
        fail_path = Path("(could not write)")
    raise RuntimeError(
        "JSON repair pass still failed to produce parseable triage JSON. "
        f"Wrote raw assistant text to {fail_path}. "
        "Retry the run; if it persists, inspect that file (often the model returned "
        "non-JSON or the wrong assistant turn was parsed)."
    ) from last_inner


def _final_triage_assistant_text(messages: list[Any]) -> str:
    """
    Use the chronologically **last** assistant message when possible.

    Scanning only for the last non-empty text can pick an earlier turn like
    'I'll use the tool…' instead of the final triage JSON.
    """
    last_ai: AIMessage | None = None
    for m in messages:
        if isinstance(m, AIMessage):
            last_ai = m
    if last_ai is None:
        raise RuntimeError("Agent returned no AIMessage")
    body = _ai_content_str(last_ai).strip()
    if body:
        return _ai_content_str(last_ai)
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
    last_ai = _final_triage_assistant_text(messages)

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
