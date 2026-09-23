# AgentShield
[CI](https://github.com/santiipm/agent-shield/actions/workflows/ci.yml/badge.svg)

## Why this exists

AgentShield is a CLI tool for evaluating AI agent security against prompt injection, indirect injection, exfiltration, and privilege escalation attacks. It was built as a portfolio project using OpenCode and a local Ollama model, meaning an AI coding agent was part of the development workflow itself.

## Quickstart

**Docker Compose** (recommended — runs AgentShield + Ollama together):

```bash
docker compose up -d                              # start AgentShield + Ollama services
docker compose exec ollama ollama pull llama3.2    # pull a model (first run only)
docker compose exec agentshield agentshield run --model llama3.2      # run prompt injection attacks
docker compose exec agentshield agentshield run-mcp --model llama3.2  # run MCP tool-poisoning attacks
docker compose exec agentshield agentshield history                   # view past runs from SQLite
```

Then visit **http://localhost:8000/dashboard/runs** in your browser to view the dashboard.

**Local (without Docker):**

```bash
pip install -e ".[dev]"
# ensure Ollama is running locally with llama3.2 pulled
agentshield run --model llama3.2
agentshield run-mcp --model llama3.2
agentshield history
agentshield serve          # starts the dashboard on http://0.0.0.0:8000
```

## Features

- **Attack categories**: prompt_injection (ignore instructions, role override, fake system message, gradual escalation), indirect_injection, exfiltration, and privilege_escalation
- **MCP security module**: tool-poisoning attacks (`agentshield run-mcp`) that decoy tool-calling agents into invoking malicious tools via poisoned tool descriptions — a distinct attack surface from text-based prompt injection
- **Hybrid evaluator**: combines a deterministic keyword evaluator with an LLM judge, surfacing disagreements for auditability instead of silently resolving to one side
- **FastAPI dashboard**: read-only endpoints (`/api/runs`, `/dashboard/*`) for viewing runs, comparisons, and history — including a separate MCP runs view
- **SQLite persistence**: every run is saved locally in `agentshield.db` for later review via `agentshield history` and `agentshield compare`
- **Structured logging**: structlog-powered output for tracing what happened during a run
- **CI**: automated lint (ruff), type check (mypy), and test (pytest) on every push and PR

## Architecture

```
Text-based attacks:
  Attack → Agent → Evaluator → Runner → Reporting / Persistence

MCP tool-poisoning attacks (separate, parallel path):
  ToolPoisoningAttack → ToolCallingAgent → ToolCallingRunner → Reporting / Persistence
```

The two paths share the same underlying philosophy (isolate failures per-attack, keep evaluation separate from execution) but deliberately do not share interfaces — text attacks evaluate free-form responses (keyword match + LLM judge), while MCP attacks evaluate a structured decision (which tool, if any, the agent called) with no ambiguity to judge. Both paths persist to the same SQLite database in separate tables, and both are visible from the dashboard.

## Local development

```bash
pip install -e ".[dev]"
ruff check .
mypy --strict src/
pytest tests/ -v
agentshield run --model llama3.2      # run attacks against a local model
agentshield serve                     # start the dashboard
```

## Notable findings

- **LLM judge inconsistency** (ADR 002): LLM judges can produce contradictory verdicts across runs even when the agent's refusal is unambiguous. The hybrid evaluator makes this disagreement visible rather than silently resolving to one side.
- **Keyword evaluator false positives** (ADR 003): The keyword evaluator can flag success when the target phrase appears incidentally (e.g., in a refusal explanation). It is deterministic but lexical — it cannot distinguish compliance from quoting.
- **MCP tool-poisoning efficacy** (ADR 004): A weakly-worded decoy tool description failed to hijack the agent, but strengthening it with authoritative, policy-like language and an innocuous tool name succeeded — attack strength, not just the presence of a malicious tool, determines outcome.

See `docs/decisions/` for the full write-up of each finding.

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.