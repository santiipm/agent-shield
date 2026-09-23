# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com),
and this project adheres to [Semantic Versioning](https://semver.org/).

## 0.2.0 — upcoming

- **Added MCP tool-poisoning security module**: `agentshield run-mcp` runs attacks that poison tool descriptions to hijack tool-calling agents into invoking decoy tools, with its own persistence, CLI, and dashboard views running in parallel to the text-attack path.
- **Added hybrid keyword+LLM-judge evaluator**: combines deterministic lexical matching with an LLM judge, surfacing disagreements for auditability instead of silently resolving to one side.
- **Added dashboard with run comparison**: FastAPI read-only server with `/api/runs`, `/dashboard/*` endpoints and a comparison view via `agentshield compare`.
- **Added Docker Compose packaging**: AgentShield + Ollama run together via `docker compose up`, so the project can be tried end-to-end without installing anything but Docker.
- **Added CI**: GitHub Actions workflow running ruff, mypy --strict, and pytest on every push and PR.
- **Added structured logging**: structlog across the runner, agents, and evaluators, with the evaluator-disagreement event logged at warning level as the most operationally relevant signal in the system.

## 0.1.0 — initial release

- **CLI tool** with commands: `agentshield run`, `history`, `compare`, `serve`, `run-mcp`, `mcp-history`.
- **Prompt injection attacks** across 4 categories: prompt_injection (ignore instructions, role override, fake system message, gradual multi-turn escalation), indirect_injection, exfiltration, and privilege_escalation.
- **Keyword evaluator**: deterministic lexical target-phrase matching.
- **LLM judge evaluator**: LLM-based verdict on attack success, with a prompt designed to resist injection from the transcript it analyzes.
- **SQLite persistence**: every run saved to `agentshield.db`, queryable via `agentshield history` and `agentshield compare`.

### Notable findings

- **ADR 002**: observed inconsistency in LLM-judge verdicts across identical runs, despite unambiguous agent refusals.
- **ADR 003**: keyword evaluator false positives when the target phrase appears in a refusal or quote rather than genuine compliance.
- **ADR 004**: tool-poisoning attack strength (wording and disguise of the malicious tool) determines success more than the mere presence of a malicious tool option.