"""Data model for storing attack evaluation results."""

from pydantic import BaseModel, Field


class AttackResult(BaseModel):
    """Structured result from evaluating an attack against an agent."""

    attack_name: str
    attack_category: str
    turns: list[str]
    responses: list[str]
    success: bool
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str
