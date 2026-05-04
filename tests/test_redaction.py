"""Unit tests for Session 2 redaction helpers."""

from __future__ import annotations

from src.redaction import redact_incident, redact_text


def test_redact_email_and_openai_key() -> None:
    s = "Contact ops@example.com; key sk-123456789012345678901234567890"
    out = redact_text(s)
    assert "ops@" not in out
    assert "[REDACTED_EMAIL]" in out
    assert "sk-123456789012345678901234567890" not in out
    assert "[REDACTED_TOKEN]" in out


def test_redact_incident_nested() -> None:
    inc = {
        "alert": {"title": "x", "detail": "user@corp.com failed"},
        "log_excerpts": ["line with AKIA0123456789ABCDEF"],
    }
    r = redact_incident(inc)
    assert r["alert"]["detail"] != inc["alert"]["detail"]
    assert "[REDACTED_EMAIL]" in r["alert"]["detail"]
    assert "[REDACTED_AWS_KEY]" in r["log_excerpts"][0]
