# Transitions

A transition compares two finite ledgers. It records what changed and which finite records witness those changes.

## Changed Coordinates

`diff_ledgers(before, after)` separates changes into:

- support
- kernel
- certificate
- obligation
- environment
- mode/scope
- provenance
- event order
- status/admissibility

## Witness Rule

Each changed coordinate should have a `TransitionWitness`. If admissibility improves from not-admissible to admissible, the gain must be traced to witnessed pre-admissibility coordinates.

Common failures:

- `transition.missing_witness`
- `transition.missing_witness_record`
- `transition.untraced_admissibility_gain`

## Review Procedure

1. Validate the previous ledger.
2. Validate the next ledger.
3. Diff the two ledgers.
4. Add witnesses for every changed coordinate.
5. Re-run transition validation.
