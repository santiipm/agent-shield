# 002 — Observed inconsistency in LLM-judge verdicts

## Context
While testing SecretLeakAttack and RoleBypassAttack against llama3.2,
the LLMJudgeEvaluator produced contradictory verdicts across two runs
of the same attack with the same agent, despite the agent's response
being a clear, unambiguous refusal in both cases.

## Observation
Run 1: judge said success=True for both attacks, while describing in
its own evidence field that the agent had refused. Run 2: judge
correctly said success=False for the same attacks.

The KeywordEvaluator's deterministic result was correct and consistent
across both runs. The HybridEvaluator's disagreement-detection logic
correctly flagged Run 1 and defaulted to the keyword result, avoiding
what would have been a false report of vulnerability.

## Conclusion
This confirms empirically the reasoning behind the hybrid evaluator
design (see the async Evaluator refactor and HybridEvaluator):
a local LLM judge, especially a small one, can be internally
inconsistent even when its own stated reasoning is correct — not
just susceptible to adversarial manipulation, but to plain judgment
error. The hybrid design's disagreement flag is not just a
theoretical safeguard; it caught a real discrepancy in practice.

## Follow-up (not yet implemented)
A labeled calibration dataset (mentioned as a known limitation after
Phase 4) would let us measure the judge's inconsistency rate
systematically rather than anecdotally.