"""Extract and repair LLM-produced JSON for ``TriageOutput`` (Sessions 1–2)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, HumanMessage

from src.schema import TriageOutput

if TYPE_CHECKING:
    from langchain_openai import ChatOpenAI


def strip_json_fence(text: str) -> str:
    text = text.strip()
    m = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text


def extract_first_json_object_str(text: str) -> str:
    """First top-level ``{ ... }`` via ``JSONDecoder.raw_decode`` (preamble / junk tolerant)."""
    text = strip_json_fence(text).strip()
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


def relax_json_commas(s: str) -> str:
    """Remove trailing commas before ``}`` or ``]`` (invalid JSON many LLMs emit)."""
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r",(\s*)([}\]])", r"\1\2", s)
    return s


def parse_triage_json(text: str) -> TriageOutput:
    cleaned = strip_json_fence(text)
    blobs: list[str] = [cleaned, relax_json_commas(cleaned)]
    try:
        ext = extract_first_json_object_str(text)
        blobs.extend([ext, relax_json_commas(ext)])
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


def ai_content_str(msg: AIMessage) -> str:
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


def repair_triage_json(
    llm: ChatOpenAI,
    bad_text: str,
    err: str,
    *,
    failure_path: Path | None = None,
) -> TriageOutput:
    """Second-pass LLM repair when the agent output is not valid ``TriageOutput`` JSON."""
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
        body = ai_content_str(out)
        if not body.strip():
            continue
        try:
            return parse_triage_json(body)
        except (json.JSONDecodeError, ValueError) as e2:
            last_inner = e2
            continue

    out_path = failure_path
    if out_path is None:
        out_path = Path(__file__).resolve().parents[1] / "triage_parse_failure.txt"
    try:
        out_path.write_text(
            f"# Last error: {err}\n# Repair errors: {last_inner!r}\n\n--- assistant text ---\n{bad_text[:50000]}",
            encoding="utf-8",
        )
    except OSError:
        out_path = Path("(could not write)")
    raise RuntimeError(
        "JSON repair pass still failed to produce parseable triage JSON. "
        f"Wrote raw assistant text to {out_path}. "
        "Retry the run; if it persists, inspect that file."
    ) from last_inner
