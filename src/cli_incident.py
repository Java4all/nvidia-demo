"""Build incident JSON for CLI / Session 4 from alert title + raw logs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_incident(
    alert_title: str,
    log_text: str | None = None,
    *,
    severity: str = "P3",
    source: str = "cli",
    fired_at: str | None = None,
    environment: str = "unknown",
    region: str = "unknown",
    service: str = "unknown",
) -> dict[str, Any]:
    """
    Shape matches ``samples/incident_01.json``: alert + context + log_excerpts.

    ``log_text`` is split into non-empty lines for ``log_excerpts``. If None or
    blank, ``log_excerpts`` is a single placeholder line so tools still run.
    """
    title = (alert_title or "").strip()
    if not title:
        raise ValueError("alert title is empty")

    if fired_at is None:
        fired_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if log_text and log_text.strip():
        excerpts = [ln for ln in log_text.splitlines() if ln.strip()]
    else:
        excerpts = ["(no log lines provided; triage from alert title and context only.)"]

    return {
        "alert": {
            "title": title,
            "severity": severity,
            "source": source,
            "fired_at": fired_at,
        },
        "context": {
            "environment": environment,
            "region": region,
            "service": service,
        },
        "log_excerpts": excerpts,
    }
