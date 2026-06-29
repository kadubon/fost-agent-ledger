# Quickstart

The ledger answers a narrow question: "What finite records support this output, and what visible limits remain?"

## Python API

```python
from fost_agent_ledger import LedgerBuilder, ModeContract, validate_ledger

builder = LedgerBuilder(agent_id="agent-1", mode="research_summary")
claim = builder.add_claim("The output summarizes a finite paper section.")
builder.add_support("The claim was checked against the paper text.", supports=[claim.id])
builder.add_issue("No independent replication check was performed.", severity="medium")
builder.add_critic_coverage(role="external_challenge", covered=True)

ledger = builder.finalize()
result = validate_ledger(ledger, mode=ModeContract.research_summary())
print(result.summary)
```

Use this path when your agent is written in Python.

## CLI

```bash
fost-ledger init --mode research_summary --agent-id agent-1 > ledger.json
fost-ledger validate ledger.json
fost-ledger explain adequacy.vacuous
```

Use this path for shell scripts, CI checks, or manual review.

## JSON Only

A minimal v1.0 ledger has a finite root:

```json
{
  "schema_version": "1.0",
  "agent_id": "agent-1",
  "mode": "draft",
  "records": [],
  "support_graph": {},
  "event_order": {"current_event": "event-0", "events": ["event-0"], "order_edges": []},
  "provenance_edges": [],
  "stage_builds": [],
  "frozen_stages": [],
  "metadata": {}
}
```

Use this path when another service or language writes ledgers.

## Reading Results

- `status` says how the finite support looks.
- `admissibility` says whether the output can be used under the selected mode.
- `errors` and `warnings` list machine-readable `Problem.code` values.
- `open_issues` and `open_obligations` show visible follow-up.

An admissible result is scoped to the finite ledger and mode. It is not a global truth or safety claim.
