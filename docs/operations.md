# Operations Runbook

## CI Checks

Run:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest
uv build
uv run python tools/audit_release.py dist
uv run python tools/check_package_metadata.py . dist
```

## Ledger Review

1. Confirm the mode is correct.
2. Check unresolved `Problem.code` values.
3. Confirm all certificate uses have registered targets and finite states.
4. Confirm open hard obligations block the output.
5. Confirm selected environment tokens are fresh enough for the mode.
6. Confirm transition witnesses exist for changed coordinates.

## Commercial Deployment Notes

- Treat the JSON Schema as the wire contract.
- Keep certificate registries target-specific.
- Store ledgers with the output they justify.
- Never treat `admissible` as a global truth or safety claim.
- Keep validator timeouts visible.
