# CLI

```bash
fost-ledger init --mode draft --agent-id agent-1
fost-ledger validate ledger.json
fost-ledger summarize ledger.json
fost-ledger schema
fost-ledger diff before.json after.json
fost-ledger explain validator.timeout
fost-ledger demo
```

- `init` prints a minimal v1.0 ledger with process, presentation, and requirement scaffolding.
- `coverage` prints manuscript-to-runtime coverage rows.
- `validate` prints a full validation result and exits with `1` when errors are present.
- `summarize` prints the validation summary.
- `schema` prints the portable JSON Schema bundle.
- `diff` compares two ledgers and validates transition witnesses.
- `explain` prints meaning, likely causes, and repair guidance for a `Problem.code`.
