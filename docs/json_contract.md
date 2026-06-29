# JSON Contract

The canonical ledger version is `1.0`.

## Ledger Root

Required fields:

- `schema_version`: always `"1.0"` for new ledgers.
- `agent_id`: the finite agent/process identifier.
- `mode`: the mode contract name.
- `records`: finite `LedgerRecord` items.
- `support_graph`: finite graph over record IDs.
- `event_order`: finite event list and order edges.

Optional but recommended fields:

- `provenance_edges`
- `stage_builds`
- `frozen_stages`
- `metadata`

## Migration

`EvaluatedLedger.from_dict` accepts v0.1, v0.2, v0.3, and v0.4 shaped ledgers and returns a v1.0 object. The migration is structural only. It does not invent evidence, certificates, witnesses, or validation results.

The migration records `metadata.migrated_from_schema_version`.

## Typed Records

Each record has:

- `id`
- `record_type`
- `stage`
- `event_id`
- `timestamp`
- `payload`

The JSON Schema defines record-type-specific payload shapes. Important v1.0 record types include:

- `process_class`
- `distinction_basis`
- `finite_presentation`
- `presentation_map`
- `finite_expression`
- `requirement_policy`
- `requirement_reason`
- `requirement_transfer`
- `settledness_declaration`
- `settledness_license`
- `obstruction_profile`
- `certificate_cover`
- `obligation_discharge`
- `obligation_lifecycle`
- `acceptance`
- `abstention`
- `failure`
- `mode_filtered_failure`
- `consistency_profile`
- `validator_timeout`
- `null_certificate`
- `respect_certificate`
- `compression_profile_class`
- `compression_factorization`
- `record_preserving_refinement`
- `self_modification_witness`
- `theory_item_coverage`

## Portable Schema

Use:

```bash
fost-ledger schema > fost-agent-ledger.schema.json
```

The schema contains definitions for:

- `EvaluatedLedger`
- `OperationalCut`
- `LedgerTransition`
- `CertificateRegistry`
- `Kernel`
- all major typed payloads
