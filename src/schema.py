"""Structured triage output (Session 1 contract)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Escalate(BaseModel):
    required: bool = Field(description="Whether to escalate to a human/on-call now")
    reason: str = Field(description="Short reason for escalation decision")


class LikelyCause(BaseModel):
    cause: str
    confidence: Literal["low", "med", "high"]
    evidence: str


class Reference(BaseModel):
    source: str
    excerpt: str


class Signals(BaseModel):
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    notable_ids: list[str] = Field(default_factory=list)


class TriageOutput(BaseModel):
    summary: str
    signals: Signals
    likely_causes: list[LikelyCause]
    next_steps: list[str]
    escalate: Escalate
    references: list[Reference] = Field(default_factory=list)
