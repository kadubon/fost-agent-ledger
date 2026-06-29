# Concepts In Plain Language

- Ledger: a finite JSON document about one agent output or process cut.
- Record: one finite item in the ledger, such as a claim, support note, issue, certificate, failure, or obligation.
- Support edge: a directed link from a supporting record to the record it supports.
- Operational cut: a snapshot of a process with its ledger, support graph, event order, kernel, certificates, and environment.
- Mode: the use case, such as `draft`, `research_summary`, `code_generation`, or `agent_action`.
- Status: how the finite support looks right now.
- Admissibility: whether this finite ledger can be used under the selected mode.
- Certificate: a finite external or internal check. It is only valid for a registered target, scope, freshness, and use kind.
- Environment token: a visible assumption about tools, models, time, data age, policy version, or external conditions.
- Residue: something outside the current presentation that remains relevant.
- Obstruction: a visible reason that a residue or failure blocks progress.
- Obligation: a follow-up item that remains open, scheduled, transferred, discharged, failed, or blocked.
- Failure: a visible failed check. It blocks only when it is relevant to the current mode.
- Acceptance: a visible record that a target is accepted after finite checks.
- Abstention: a visible decision not to proceed. It can still be obstructed.
- Consistency profile: a finite list of typed coordinates that passed, failed, or are missing.
- Transition: the difference between two ledgers, with witnesses for changed coordinates.
- Problem code: a machine-readable explanation of why validation did not pass.

## Important Boundaries

- The ledger does not know the hidden true state of the world.
- Missing facts stay missing until represented as records.
- Unavailable leaves can stop a support search, but they are not evidence.
- Chain-of-thought is not required. Use visible summaries, issues, residues, and provenance references.
