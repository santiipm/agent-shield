"""Pydantic response models for the read-only API."""

from datetime import datetime

from pydantic import BaseModel


class RunSummary(BaseModel):
    """Summary of a single evaluation run."""

    id: int
    timestamp: datetime
    model: str


class AttackResultSummary(BaseModel):
    """Summary of a single attack result."""

    attack_name: str
    attack_category: str
    success: bool
    confidence: float
    error: str | None = None


class RunDetail(RunSummary):
    """Full run detail including all attack results."""

    results: list[AttackResultSummary]


class CompareEntry(BaseModel):
    """One row in a run-vs-run comparison."""

    attack_name: str
    run_1_success: bool | None
    run_2_success: bool | None
    verdict: str
