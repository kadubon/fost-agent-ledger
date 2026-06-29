# Contributing

Use `uv` for development:

```bash
uv sync
uv run ruff format .
uv run ruff check .
uv run mypy src
uv run pytest
```

Keep changes small and test behavior that affects public API, serialization, or validation results. Do not add AI-provider-specific runtime dependencies to the core package.
