# fost-agent-ledger

`fost-agent-ledger` is a small Python toolkit for recording the visible support behind an AI-agent output. It writes down what was claimed, what evidence or certificate was used, what remains uncertain, which obligations are still open, and what changed between two runs.

It is based on Takahashi, K. (2026), *Finite Operational Structure Theory: A Mathematical Theory of Finite Operational Cuts*, DOI: [10.5281/zenodo.20995846](https://doi.org/10.5281/zenodo.20995846).

## What Problem This Solves

Agent outputs often look final even when they depend on limited evidence, stale tools, missing checks, or unresolved assumptions. This package gives you a portable ledger for those finite facts. It does not prove truth or safety. It makes the visible support, limits, and required follow-up explicit.

Use it when you want an agent, review pipeline, or evaluation script to answer practical questions such as:

- What records support this output?
- Which assumptions, certificates, or tool conditions were used?
- What remains unresolved or intentionally out of scope?
- Did the support change between the previous run and this run?
- Is the output admissible under a chosen mode such as `draft`, `research_summary`, or `safety_sensitive_advice`?

## Install

```bash
pip install fost-agent-ledger
python -c "import fost_agent_ledger as f; print(f.__version__)"
fost-ledger init --mode research_summary --agent-id agent-1
```

## 3-Minute Python Quickstart

```python
from fost_agent_ledger import LedgerBuilder, ModeContract, validate_ledger

builder = LedgerBuilder(agent_id="agent-1", mode="research_summary")
claim = builder.add_claim("The report summarizes the paper's main boundary claims.")
builder.add_support("The summary was checked against the introduction and appendix.", supports=[claim.id])
builder.add_issue("No external replication check was performed.", severity="medium")
builder.add_critic_coverage(role="external_challenge", covered=True)

result = validate_ledger(builder.finalize(), mode=ModeContract.research_summary())
print(result.summary)
```

The output tells you whether the finite ledger is supported and admissible for the selected mode.
For a publishable checked ledger, use `builder.finalize_checked()` and validate with
`validate_ledger(ledger, require_finality=True)`. That stricter path requires separate finite
records for the status body, checked status, pre-admissibility support vector, admissibility body,
checked admissibility, adequacy dispositions, anchor declarations, and kernel context.

## 3-Minute CLI Quickstart

```bash
fost-ledger init --mode research_summary --agent-id agent-1 > ledger.json
fost-ledger validate ledger.json
fost-ledger validate ledger.json --require-finality
fost-ledger explain validator.timeout
fost-ledger coverage
```

The CLI is useful in CI, evaluation jobs, and manual review because the output is JSON and the problem codes are stable.
Unknown modes fail closed by default. Use `--allow-unknown-mode-as-draft` only when you explicitly
want draft fallback semantics.

## Three Ways To Use It

- Python API: use `LedgerBuilder` and `validate_ledger` inside an agent or evaluation pipeline.
- CLI: run `fost-ledger init`, `fost-ledger validate`, `fost-ledger diff`, and `fost-ledger explain CODE`.
- JSON only: write canonical `schema_version: "2.0"` ledgers and validate them with the exported JSON Schema.
- Strict finality: require a checked output path with `require_finality=True` or
  `fost-ledger validate --require-finality`.

## What A Ledger Contains

A ledger is finite JSON. Typical records include:

- claims and support summaries;
- provenance and event order;
- evidence state and unavailable evidence leaves;
- certificate targets, uses, and states;
- issues, residues, obstructions, and obligations;
- environment tokens such as data age or tool state;
- transition witnesses for changed support, kernel, certificate, or environment coordinates.

## Common Commands

```bash
fost-ledger init --mode research_summary --agent-id agent-1
fost-ledger validate ledger.json
fost-ledger summarize ledger.json
fost-ledger diff before.json after.json
fost-ledger explain validator.timeout
fost-ledger coverage
fost-ledger schema
```

## What It Does Not Do

It is not a truth verifier, universal safety guarantee, moral evaluator, or chain-of-thought recorder. It stores visible claims, support summaries, provenance, certificates, issues, residues, obligations, environment tokens, failures, and transition witnesses.

The implementation target is complete finite operational coverage: every tracked manuscript item is represented by finite record types, validators, witnesses, `Problem` codes, tests, or explicit design-boundary docs. It does not add a theorem prover because FOST treats hidden truth states and completed infinities as outside the runtime contract.

## Why It Is Different

Most agent audit logs store a transcript or a score. `fost-agent-ledger` stores a finite operational cut: a typed, portable, mode-scoped record of what the output is allowed to rely on and what remains unresolved. That makes it useful for review, regression testing, compliance evidence, and agent-to-agent handoff without claiming more certainty than the recorded support provides.

## Read Next

- [Documentation Index](docs/index.md): recommended reading order.
- [Quickstart](docs/quickstart.md): Python, CLI, and JSON paths.
- [Concepts](docs/concepts.md): plain-language glossary.
- [Workflows](docs/workflows.md): practical mode-specific recipes.
- [Problem Codes](docs/problem_codes.md): how to fix validator output.
- [JSON Contract](docs/json_contract.md): v2.0 schema and migration.
- [Theory Mapping](docs/theory_mapping.md): manuscript-to-implementation coverage.
- [Release And PyPI Publishing](docs/release.md): Trusted Publishing setup and release checks.

## License

Apache License 2.0.
