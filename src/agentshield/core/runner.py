"""Runner for orchestrating security evaluation attacks."""

from agentshield.core.agent import Agent
from agentshield.core.attack import Attack
from agentshield.core.evaluator import Evaluator
from agentshield.core.result import AttackResult
from collections.abc import Sequence


class Runner:
    """Orchestrates Attack -> Agent -> Evaluator flow with failure isolation."""

    async def run(
        self, agent: Agent, attacks: Sequence[Attack], evaluator: Evaluator
    ) -> list[AttackResult]:
        """Execute all attacks and collect results, isolating failures per attack."""
        results: list[AttackResult] = []

        for attack in attacks:
            try:
                turns = attack.generate()
                responses: list[str] = []

                for turn in turns:
                    response = await agent.invoke(turn)
                    responses.append(response)

                result = await evaluator.evaluate(attack, turns, responses)
                results.append(result)

            except Exception as e:
                result = AttackResult(
                    attack_name=attack.name,
                    attack_category=attack.category,
                    turns=turns if "turns" in locals() else [],
                    responses=responses if "responses" in locals() else [],
                    success=False,
                    confidence=0.0,
                    evidence="",
                    error=str(e),
                )
                results.append(result)

        return results
