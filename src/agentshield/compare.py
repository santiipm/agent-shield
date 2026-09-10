"""Shared comparison logic for run-vs-run analysis."""

from agentshield.api.schemas import CompareEntry


def compare_runs(
    results_1: list[dict[str, object]],
    results_2: list[dict[str, object]],
) -> list[CompareEntry]:
    """Compare two lists of attack results and classify each attack.

    Returns one CompareEntry per unique attack name across both result sets,
    with a verdict of IMPROVED, REGRESSED, UNCHANGED, or N/A.
    """
    attacks_1: dict[str, bool] = {
        str(r["attack_name"]): bool(r["success"]) for r in results_1
    }
    attacks_2: dict[str, bool] = {
        str(r["attack_name"]): bool(r["success"]) for r in results_2
    }

    all_attack_names = sorted(set(attacks_1) | set(attacks_2))

    entries: list[CompareEntry] = []
    for attack_name in all_attack_names:
        in_1 = attack_name in attacks_1
        in_2 = attack_name in attacks_2

        if in_1 and in_2:
            success_1 = attacks_1[attack_name]
            success_2 = attacks_2[attack_name]
            if success_1 and not success_2:
                verdict = "IMPROVED"
            elif not success_1 and success_2:
                verdict = "REGRESSED"
            else:
                verdict = "UNCHANGED"
            entries.append(
                CompareEntry(
                    attack_name=attack_name,
                    run_1_success=success_1,
                    run_2_success=success_2,
                    verdict=verdict,
                )
            )
        elif in_1:
            entries.append(
                CompareEntry(
                    attack_name=attack_name,
                    run_1_success=attacks_1[attack_name],
                    run_2_success=None,
                    verdict="N/A",
                )
            )
        else:
            entries.append(
                CompareEntry(
                    attack_name=attack_name,
                    run_1_success=None,
                    run_2_success=attacks_2[attack_name],
                    verdict="N/A",
                )
            )

    return entries
