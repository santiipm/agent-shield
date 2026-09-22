"""JSON report generator for MCP tool-poisoning results."""

import json
from datetime import datetime
from pathlib import Path

from agentshield.mcp.models import ToolCallResult


def save_mcp_report(
    results: list[ToolCallResult], output_dir: str = "results"
) -> str:
    """Save MCP attack results to a timestamped JSON file.

    Args:
        results: List of MCP tool call results to save.
        output_dir: Directory to write the report file to.

    Returns:
        Full path to the written file.
    """
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = path / f"mcp_run_{timestamp}.json"

    data = [result.model_dump(mode="json") for result in results]
    file_path.write_text(json.dumps(data, indent=2))

    return str(file_path)
