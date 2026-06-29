# Problem Codes

Validators return machine-readable `Problem.code` values. Use:

```bash
fost-ledger explain validator.timeout
```

## v1.0 Executable-Theory Codes

| Code | Meaning | Repair |
| --- | --- | --- |
| `abstention.obstructed` | Abstention is visible but obstructed. | Record the obstruction or keep inadmissible. |
| `acceptance.blocked` | Accepted target still has blockers. | Resolve blockers before accepting. |
| `acceptance.missing_target` | Acceptance points at no record. | Add or correct the target record. |
| `admissibility.checked_status_leakage` | Admissibility used checked status as input. | Use a pre-admissibility body/vector. |
| `admissibility.unchecked_status_license` | Unchecked status licensed admissibility. | Create checked status separately. |
| `certificate.kernel_circular_support` | Certificate/kernel support is circular. | Use prior kernel or external anchor. |
| `certificate.cover_cycle` | Certificate cover is circular. | Use independent certificate-state support before cover. |
| `certificate.null_misuse` | Null certificate was used as license. | Use a real target-scoped certificate. |
| `certificate.role_stage_violation` | Certificate target stage is incompatible. | Target the checked-stage record. |
| `certificate.support_cycle` | Certificate support is circular. | Use an acyclic certificate-state path. |
| `compression.exactness_violation` | Compression hides an admissibility difference. | Refine compression or preserve the predicate. |
| `compression.factorization_missing` | Compression lacks a factorization witness. | Add `beta_by_value` for each compressed value. |
| `consistency.profile_incomplete` | Consistency profile has failed/missing coordinates. | Fill or repair coordinates. |
| `environment.policy_generation_cycle` | Environment token and obligation generate each other. | Make environment an external input or move obligation later. |
| `evidence.failure_laundering` | Failed evidence was hidden by an obligation. | Keep failure visible or add independent support. |
| `failure.filtered_blocks` | Mode-filtered failure blocks current mode. | Resolve or change scope/mode. |
| `failure.mode_relevant_blocks` | Relevant unresolved failure blocks current mode. | Resolve, mark irrelevant with support, or keep inadmissible. |
| `finality.output_leakage` | Final checked output was read as input. | Use pre-final bodies and witnesses only. |
| `gate.cycle` | Gate requirement/pass are circular. | Make pass depend on earlier requirement only. |
| `obligation.discharge_cycle` | Obligation discharge is circular. | Use earlier cover/support before discharge. |
| `obligation.hard_lifecycle_conflict` | Hard obligation has conflicting lifecycle records. | Resolve lifecycle or block output. |
| `obligation.invalid_transition` | Obligation lifecycle transition is invalid. | Use an allowed transition or record conflict. |
| `obligation.lifecycle_conflict` | Obligation has incompatible lifecycle targets in one event. | Split events or resolve conflict. |
| `obstruction.critical_undischarged` | Critical obstruction remains open. | Add cover/discharge or keep blocked. |
| `presentation.expression_outside_scope` | Expression or map refers outside presentation scope. | Add scoped refs or remove them. |
| `presentation.unmapped_distinction` | Presentation map or basis is incomplete. | Declare and map each required distinction. |
| `policy.generated_obligation_omission` | Gate requires missing obligation. | Add obligation or remove requirement with reason. |
| `policy.self_reference` | Policy-stage record cites itself. | Move support to an earlier finite record. |
| `process_class.missing_registry` | Process class registry is missing or incompatible. | Add a compatible `process_class` record. |
| `requirement.missing_empty_reason` | Empty requirement set lacks reason. | Record why no requirements were emitted. |
| `requirement.missing_reason` | Requirement lacks reason. | Add `requirement_reason` or reason text. |
| `requirement.missing_transfer_reason` | Requirement transfer lacks reason. | Record the transfer reason. |
| `requirement.unanswered_issue` | Requirement issue lacks visible disposition. | Add/mark issue as answered, pending, carried, or unresolved. |
| `respect.missing_coordinates` | Respect certificate omits coordinates. | Add missing respected coordinates. |
| `respect.status_admissibility_mismatch` | Admissibility does not preserve status respect. | Copy required respect coordinates or keep inadmissible. |
| `self_modification.missing_lineage` | Self-modification lacks lineage. | Add lineage record or reason. |
| `self_modification.missing_rule_disclosure` | Self-modification lacks rule/checker disclosure. | Declare versions and check disposition. |
| `settledness.license_cycle` | Settledness license is circular. | Use independent lower-stage support. |
| `settledness.unlicensed` | Settled distinction lacks license. | Add non-circular license or keep residue. |
| `transition.record_not_preserved` | Refinement drops records. | Preserve, archive, or trace records. |
| `validator.timeout` | Blocking validator timeout remains. | Rerun, waive visibly, or keep recheckable. |
| `validator.timeout_hidden` | Validator timeout was hidden. | Keep timeout visible and blocking. |

## Existing Core Codes

The package also returns core codes such as `support.cycle`, `support.missing_witness`, `certificate.missing_target`, `certificate.expired`, `kernel.self_certification`, `stage.rewrite`, `adequacy.vacuous`, and `transition.untraced_admissibility_gain`.
