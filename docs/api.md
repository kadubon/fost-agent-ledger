# API

Primary imports:

```python
from fost_agent_ledger import (
    LedgerBuilder,
    ModeContract,
    validate_ledger,
    assess_output,
    diff_ledgers,
    validate_transition,
    explain_problem,
)
```

Use `LedgerBuilder` for common agent-output ledgers. Use dataclasses directly when another language or service writes canonical JSON.

## Builder Helpers

Important helpers include:

- `add_claim`
- `add_support`
- `add_issue`
- `add_obligation`
- `add_obligation_lifecycle`
- `add_environment_token`
- `add_certificate`, `add_certificate_target`, `add_certificate_use`
- `add_failure`
- `add_acceptance`
- `add_abstention`
- `add_validator_timeout`
- `add_consistency_profile`
- `add_null_certificate`
- `add_respect_certificate`
- `add_anchor_declaration`
- `add_adequacy_record`
- `add_kernel_admission`
- `add_status_body`, `add_checked_status`
- `add_pre_admissibility_support_vector`
- `add_admissibility_body`, `add_checked_admissibility`
- `finalize_checked`

## Validation

```python
result = validate_ledger(ledger, mode=ModeContract.research_summary())
if result.errors:
    for problem in result.errors:
        print(problem.code, problem.message)
```

Strict finality:

```python
ledger = builder.finalize_checked()
result = validate_ledger(ledger, require_finality=True)
```

Unknown mode names raise `UnknownModeError` by default. Pass
`allow_unknown_mode_as_draft=True` only for explicit draft fallback.

## Transitions

```python
transition = diff_ledgers(before, after)
problems = validate_transition(before, after, transition)
```
