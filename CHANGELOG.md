# Changelog

## 2.0.0

- Promoted canonical ledgers to `schema_version: "2.0"` while retaining structural migration from v0.1-v1.0 ledgers.
- Added strict finality validation with typed status body, checked status, pre-admissibility support vector, admissibility body, checked admissibility, persisted adequacy records, typed anchor declarations, and kernel context checks.
- Made unknown mode handling fail closed by default; explicit draft fallback is available through API/CLI opt-in.
- Hardened certificate scope coverage so missing scope keys no longer silently cover constrained targets.
- Added public builder helpers for checked finalization, finality records, anchor declarations, adequacy records, and kernel admissions.

## 1.0.0

- Promoted the package to the stable v1.0.0 release and canonical ledger `schema_version` to `"1.0"`.
- Kept v0.1/v0.2/v0.3/v0.4 structural migration into the v1.0 canonical JSON contract.
- Strengthened theory coverage auditing so all 184 manuscript items have machine-checkable runtime, schema, docs, and test anchors.
- Added README `pip install fost-agent-ledger` guidance for PyPI users.
- Preserved the finite-operational implementation boundary: no hidden truth state, no global safety primitive, and no external theorem prover.

## 0.4.2

- Added machine-checkable theory coverage anchors and an optional TeX registry audit.
- Added public release artifact and package metadata audits for PyPI distribution hygiene.
- Prepared PyPI Trusted Publishing through GitHub Actions using OIDC and the `pypi` environment.
- Updated project URLs to `kadubon/fost-agent-ledger` and kept canonical ledger schema at `0.4`.

## 0.4.1

- Added a TeX-derived independent theory coverage registry with 184 manuscript items.
- Moved `fost-ledger coverage` off the docs table and onto packaged registry data.
- Added DOI documentation for `https://doi.org/10.5281/zenodo.20995846`.
- Added registry/docs/problem/schema sync tests for commercial hardening.
- Kept canonical ledger `schema_version` at `"0.4"` for backward-compatible v0.4 hardening.

## 0.4.0

- Breaking v0.4 JSON/core release focused on executable-theory completion.
- Added typed records and payloads for process classes, distinction bases, finite presentations, presentation maps, finite expressions, requirement policies/reasons/transfers, settledness declarations/licenses, obstruction profiles, certificate cover, obligation discharge, compression profile classes/factorizations, record-preserving refinements, self-modification witnesses, and theory item coverage.
- Added validators for process-class registry compatibility, presentation totality/scope, requirement reason obligations, licensed settledness, critical obstruction discharge, null certificate misuse, cover/discharge cycles, record preservation, self-modification lineage/rule disclosure, and finite compression exactness/factorization.
- Added `fost-ledger coverage` and upgraded `fost-ledger init` to emit a v0.4 scaffold.
- Updated JSON Schema, problem-code catalog, and theory mapping so all tracked manuscript items have implemented runtime or design-boundary anchors.

## 0.3.0

- Breaking v0.3 JSON/core release focused on formal completion and first-use documentation.
- Added typed records and payloads for obligation lifecycle, acceptance, abstention, failures, mode-filtered failures, consistency profiles, validator timeouts, null certificates, and respect certificates.
- Added formal-completion validators for lifecycle conflicts, gate cycles, failure filtering, respect mismatch, timeout leakage, certificate/kernel circular support, evidence failure laundering, and related countermodels.
- Added `fost-ledger init` and `fost-ledger explain CODE`.
- Expanded JSON Schema with v0.3 canonical ledger, transition, certificate registry, kernel, and new payload definitions.
- Added practical Docs for quickstart, workflows, JSON contract, problem codes, certificates, transitions, and operations.

## 0.2.0

- Breaking core/JSON release focused on formal-completeness hardening.
- Added canonical v0.2 ledger root fields: `schema_version`, event order, provenance edges, stage-build records, support validation coordinates, and anchor role metadata.
- Added typed payload models and stricter JSON Schema definitions for major record types.
- Hardened support, certificate, kernel, stage, status/admissibility, environment, and transition validators with machine-readable `Problem` codes.
- Added finality model objects for status bodies, checked status, admissibility bodies, checked admissibility, respect records, and pre-admissibility support vectors.
- Added v0.1-to-v0.2 structural migration for legacy ledger JSON.
- Updated docs to emphasize finite operational assurance, residue/horizon preservation, and non-truth/non-safety boundaries.

## 0.1.0

- Initial package structure.
- Added finite ledger models, support graph validation, certificate target checks, obligation and environment checks, mode contracts, transition validation, CLI, examples, docs, and CI workflows.
