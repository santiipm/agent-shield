"""Runner for orchestrating tool-poisoning attacks with failure isolation."""

from collections.abc import Sequence

from agentshield.mcp.agent import ToolCallingAgent
from agentshield.mcp.attack import ToolPoisoningAttack
from agentshield.mcp.models import ToolCallDecision, ToolCallResult


class ToolCallingRunner:
    """Orchestrates ToolPoisoningAttack -> ToolCallingAgent flow."""

    async def run(
        self,
        agent: ToolCallingAgent,
        attacks: Sequence[ToolPoisoningAttack],
    ) -> list[ToolCallResult]:
        """Execute all attacks and collect results, isolating failures per attack."""
        results: list[ToolCallResult] = []

        for attack in attacks:
            try:
                message = attack.user_message()
                tools = attack.poisoned_tools()
                decision = await agent.invoke_with_tools(message, tools)
                compromised = attack.is_compromised(decision)

                if compromised:
                    evidence = f"Agent called tool '{decision.tool_name}'"
                elif decision.tool_name is not None:
                    evidence = (
                        f"Agent called tool '{decision.tool_name}' "
                        "(not the poisoned target)"
                    )
                elif decision.text_response is not None:
                    evidence = "Agent responded with text instead of calling a tool"
                else:
                    evidence = "Agent made no tool call and gave no text response"

                results.append(
                    ToolCallResult(
                        attack_name=attack.name,
                        category=attack.category,
                        user_message=message,
                        offered_tools=[t.name for t in tools],
                        decision=decision,
                        compromised=compromised,
                        evidence=evidence,
                        error=None,
                    )
                )
            except Exception as e:
                error_msg = str(e)
                user_msg = ""
                tool_names: list[str] = []
                try:
                    user_msg = attack.user_message()
                    tool_names = [t.name for t in attack.poisoned_tools()]
                except Exception:
                    pass
                results.append(
                    ToolCallResult(
                        attack_name=attack.name,
                        category=attack.category,
                        user_message=user_msg,
                        offered_tools=tool_names,
                        decision=ToolCallDecision(
                            tool_name=None, arguments={}, text_response=None
                        ),
                        compromised=False,
                        evidence="",
                        error=error_msg,
                    )
                )

        return results
