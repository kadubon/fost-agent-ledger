# Design

The core package uses standard-library dataclasses and enums. Runtime dependencies are intentionally empty.

The paper DOI is [10.5281/zenodo.20995846](https://doi.org/10.5281/zenodo.20995846).

Design rules:

- stable lowercase enum values;
- explicit JSON serialization;
- canonical v2.0 ledgers carry `schema_version`, event order, provenance edges, stage-build records, support graph coordinates, theory coverage metadata, and typed payloads;
- no hidden global state;
- validator functions return machine-readable `Problem` objects;
- policies are separate from the domain model;
- certificates are target-indexed and must be checked through target state, finite certificate-state nodes, scope, freshness, and role-compatible support;
- certificate scope is fail-closed: missing keys do not cover constrained targets, and wildcard coverage must be explicit;
- support anchors used by strict finality require typed `anchor_declaration` records;
- validation kernel and object kernel are distinct, and kernel admissions require root debt, prior-kernel witness, or external certificate anchors;
- status and admissibility are separate outputs, with separate body/checked objects, a pre-admissibility support vector, persisted adequacy dispositions, and no final self-reference;
- transition validation compares support, kernel, certificate, obligation, environment, provenance, event-order, and mode/scope coordinates.
- v2.0 includes executable-theory records for process classes, distinction bases, finite presentations, presentation maps, finite expressions, requirement policies, settledness licenses, certificate cover, obligation discharge, compression factorization, record-preserving refinement, self-modification witnesses, and theory item coverage.
- complete implementation means every tracked manuscript item has finite runtime coverage or an explicit design-boundary anchor; it does not mean adding hidden truth, safety, objectivity, or completed-infinity primitives.

## Appendix-Driven Implementation Principles

- No essence claims: records describe finite operational objects and checks, not what an object "really is".
- No completed infinity: validators terminate over explicit finite ledgers, support graphs, registries, and event orders.
- No hidden true state: absent world facts remain absent until represented as records, residues, obstructions, environment tokens, or transition evidence.
- Horizon as residue: presentation gaps are preserved as residue/obstruction/obligation records rather than erased.
- Bounded assurance only: `admissible` means usable under a finite mode contract and ledger, not globally true or safe.
- No scalar consistency shortcut: typed consistency coordinates remain separable, so a pass/fail result keeps inspectable causes.
