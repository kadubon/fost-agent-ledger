# Limitations

This package does not verify truth, guarantee safety, or prove objective reality. It does not require chain-of-thought disclosure. It records finite support, omissions, certificates, issues, obligations, environment assumptions, and transition witnesses.

The paper DOI is [10.5281/zenodo.20995846](https://doi.org/10.5281/zenodo.20995846).

The default validators are conservative practical checks. High-assurance deployments should define project-specific mode contracts, certificate registries, kernel admission policies, environment freshness rules, and transition review processes.

Important boundaries:

- A valid ledger is not a complete world model.
- A passed certificate is only valid for its registered target, scope, freshness, and use kind.
- An unavailable leaf can terminate a finite closure, but it cannot become evidence.
- An admissibility result does not imply hidden safety, hidden truth, or hidden objective goodness.
- Transition witnesses explain finite coordinate changes; they do not prove that no external change occurred.
- The package intentionally avoids storing chain-of-thought. Use visible claims, evidence summaries, issues, residues, obligations, and provenance references instead.
- The runtime does not mechanize the manuscript's mathematical proofs. This is a design boundary, not an implementation gap: runtime completeness means finite record types, validators, witnesses, `Problem` codes, tests, and explicit boundary documentation for all tracked manuscript items.
- Project-specific policies may still be needed for regulated deployment.
