"""Mask common secrets and PII in incident/log text before sending to an LLM (Session 2)."""

from __future__ import annotations

import copy
import re
from typing import Any


EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    re.IGNORECASE,
)
# JWT-like three base64url segments
JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
# AWS access key id
AWS_KEY_RE = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
# OpenAI-style secret key prefix
OPENAI_SK_RE = re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")
# Generic high-entropy hex blob (API keys, hashes) — length >= 32
LONG_HEX_RE = re.compile(r"\b[0-9a-fA-F]{32,}\b")
# Bearer / Basic tokens in log lines
BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._\-]+\b", re.IGNORECASE)
BASIC_RE = re.compile(r"\bBasic\s+[A-Za-z0-9+/=]{16,}\b")
# Credit-card-like 13–19 consecutive digits (simple Luhn-agnostic mask)
CC_RUN_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def redact_text(s: str) -> str:
    """Apply masking rules; order matters (more specific first)."""
    out = s
    out = EMAIL_RE.sub("[REDACTED_EMAIL]", out)
    out = JWT_RE.sub("[REDACTED_JWT]", out)
    out = AWS_KEY_RE.sub("[REDACTED_AWS_KEY]", out)
    out = OPENAI_SK_RE.sub("[REDACTED_TOKEN]", out)
    out = BEARER_RE.sub("Bearer [REDACTED_TOKEN]", out)
    out = BASIC_RE.sub("Basic [REDACTED_TOKEN]", out)
    out = CC_RUN_RE.sub("[REDACTED_PAN]", out)
    out = LONG_HEX_RE.sub("[REDACTED_HEX]", out)
    return out


def redact_value(obj: Any) -> Any:
    if isinstance(obj, str):
        return redact_text(obj)
    if isinstance(obj, list):
        return [redact_value(x) for x in obj]
    if isinstance(obj, dict):
        return {k: redact_value(v) for k, v in obj.items()}
    return obj


def redact_incident(incident: dict[str, Any]) -> dict[str, Any]:
    """Deep-copy and redact all string leaves (alert, context, log lines, etc.)."""
    return copy.deepcopy(redact_value(incident))
