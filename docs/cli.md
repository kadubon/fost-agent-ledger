# CLI

```bash
fost-ledger init --mode draft --agent-id agent-1
fost-ledger validate ledger.json
fost-ledger validate ledger.json --require-finality
fost-ledger summarize ledger.json
fost-ledger schema
fost-ledger diff before.json after.json
fost-ledger explain validator.timeout
fost-ledger demo
```

- `init` prints a minimal v2.0 ledger with process, presentation, and requirement scaffolding.
- `coverage` prints manuscript-to-runtime coverage rows.
- `validate` prints a full validation result and exits with `1` when errors are present.
- `validate --require-finality` requires typed status/admissibility finality records, persisted adequacy records, typed anchors, and kernel context.
- `validate --allow-unknown-mode-as-draft` is the only way to use draft fallback for an unknown mode.
- `summarize` prints the validation summary.
- `schema` prints the portable JSON Schema bundle.
- `diff` compares two ledgers and validates transition witnesses.
- `explain` prints meaning, likely causes, and repair guidance for a `Problem.code`.
