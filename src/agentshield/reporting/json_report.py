"""JSON report generator for attack results."""

import json
from datetime import datetime
from pathlib import Path

from agentshield.core.result import AttackResult


def save_report(
    results: list[AttackResult], output_dir: str = "results"
) -> str:
    """Save attack results to a timestamped JSON file.

    Args:
        results: List of attack results to save.
        output_dir: Directory to write the report file to.

    Returns:
        Full path to the written file.
    """
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = path / f"run_{timestamp}.json"

    data = [result.model_dump() for result in results]
    file_path.write_text(json.dumps(data, indent=2))

    return str(file_path)
