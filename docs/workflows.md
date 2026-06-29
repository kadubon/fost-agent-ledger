# Workflows

## Research Summary

Use when the agent summarizes papers, documents, or logs.

Recommended records:

- `claim` for the summary statement.
- `support` or `evidence` for the checked source.
- `issue` for missing external review or uncertainty.
- `critic_coverage` when a required challenge role was used.
- `obligation` for recheck conditions.

Validation goal: visible support and visible caveats can still be admissible.

## Code Generation

Use when the output is code or a patch.

Recommended records:

- `claim` for what the code does.
- `support` for source files, tests, and assumptions.
- `environment_token` for toolchain, model, package, and policy versions.
- `validator_timeout` if tests or analysis timed out.
- `failure` for failing tests or known defects.
- `obligation` for follow-up review.

Validation goal: unresolved relevant failures or hidden timeouts should block admissibility.

## Agent Action

Use when an agent will act in an external system.

Recommended records:

- `impact_record` for impact classification.
- `certificate_target`, `certificate_use`, and `certificate_state` for permission checks.
- `gate_requirement` and `gate_pass` for action gates.
- `acceptance` or `abstention` for final action disposition.
- `transition_witness` when moving from planning to action.

Validation goal: no untraced admissibility gain, no circular gate, and no missing certificate target.

## Safety-Sensitive Advice

Use when wrong output could materially affect health, finance, legal, safety, or operational risk.

Recommended records:

- `environment_token` with selected freshness/data-age tokens.
- `impact_record` with supported high/low impact.
- `scope_exclusion` for what is not covered.
- `failure` for any unresolved check failure.
- `obligation` for recheck/escalation.
- `certificate` only for explicit registered targets.

Validation goal: unknown high-impact assumptions and unresolved known exclusions should block.
