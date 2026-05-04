"""Deterministic helpers exposed as agent tools (Session 1)."""

from __future__ import annotations

import re
from langchain_core.tools import tool


@tool
def extract_timestamps_and_ids(log_text: str) -> str:
    """Extract ISO-like timestamps and bracketed request/correlation ids from log lines."""
    times = re.findall(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", log_text)
    ids = re.findall(r"\[(req-[a-z0-9]+|[a-zA-Z0-9-]{8,})\]", log_text, flags=re.IGNORECASE)
    uniq_t = sorted(set(times))
    uniq_i = sorted(set(ids))
    return f"timestamps: {uniq_t}\nids: {uniq_i}"


@tool
def classify_severity_keywords(log_text: str) -> str:
    """Heuristic: count ERROR vs WARN lines and note timeout-style tokens."""
    lines = [ln for ln in log_text.splitlines() if ln.strip()]
    errors = sum(1 for ln in lines if re.search(r"\bERROR\b", ln))
    warns = sum(1 for ln in lines if re.search(r"\bWARN\b", ln))
    timeoutish = bool(re.search(r"Timeout|timed?\s*out|latency_ms=\d{4,}", log_text, re.I))
    return f"error_lines={errors}, warn_lines={warns}, timeoutish={timeoutish}"


@tool
def stub_lookup_playbook(alert_title: str) -> str:
    """Stub runbook lookup — Session 1–2; Session 3 uses ``lookup_runbook_rag`` in ``tools_rag``."""
    title = (alert_title or "").lower()
    if "checkout" in title or "payment" in title:
        return (
            "playbook=payments-dependency v0 (stub): "
            "1) Check payments-gw SLO and error budget. "
            "2) Compare p95 latency vs SLO. "
            "3) Verify recent deploys to checkout-api and payments-gw."
        )
    return "playbook=generic-incident v0 (stub): gather logs, metrics, and recent changes."


TOOLS = [
    extract_timestamps_and_ids,
    classify_severity_keywords,
    stub_lookup_playbook,
]
