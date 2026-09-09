"""Data models for tool-calling attack results."""

from pydantic import BaseModel


class ToolDefinition(BaseModel):
    """Description of a tool the agent may choose to invoke."""

    name: str
    description: str
    parameters: dict[str, object]


class ToolCallDecision(BaseModel):
    """What the agent decided to do when offered a set of tools."""

    tool_name: str | None = None
    arguments: dict[str, object] = {}
    text_response: str | None = None


class ToolCallResult(BaseModel):
    """Outcome of evaluating a tool-calling attack against an agent."""

    attack_name: str
    category: str
    user_message: str
    offered_tools: list[str]
    decision: ToolCallDecision
    compromised: bool
    evidence: str
    error: str | None = None
