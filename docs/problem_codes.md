# Problem Codes

Validators return machine-readable `Problem.code` values. Use:

```bash
fost-ledger explain validator.timeout
```

## v2.0 Executable-Theory Codes

| Code | Meaning | Repair |
| --- | --- | --- |
| `abstention.obstructed` | An abstention is visible, but an obstruction prevents treating it as clean closure. | Record the obstruction as an issue/residue or keep the ledger inadmissible. |
| `acceptance.blocked` | An acceptance record says a target is accepted while blockers remain. | Resolve or remove the blockers before setting accepted=true. |
| `acceptance.missing_target` | An acceptance record points at no finite ledger record. | Add the target record or correct the target_id. |
| `adequacy.missing_checker_or_rule_version` | A persisted adequacy record lacks checker or rule version. | Record finite checker and rule version identifiers. |
| `adequacy.missing_record` | Strict finality requires persisted adequacy evidence for a mode component. | Add an adequacy_record for the component or use LedgerBuilder.finalize_checked(). |
| `adequacy.record_not_accepted` | A persisted adequacy record is not accepted for strict finality. | Repair the component or record a supported waiver. |
| `adequacy.waiver_missing_support` | An adequacy waiver lacks finite support or reason. | Add support_refs or a visible reason for the waiver. |
| `admissibility.checked_status_leakage` | Admissibility used final checked status as an input. | Point admissibility at a pre-admissibility body/vector instead. |
| `admissibility.empty_pre_vector` | Checked admissibility has no finite pre-admissibility coordinates. | Record support, validator, kernel, certificate, environment, obligation, or adequacy coordinates. |
| `admissibility.missing_body` | Checked admissibility does not point at an admissibility body. | Add an admissibility_body record and point checked_admissibility at it. |
| `admissibility.missing_checker_or_rule_version` | Admissibility finality lacks checker or rule version. | Record finite checker and rule version identifiers. |
| `admissibility.missing_pre_vector` | Checked admissibility lacks a pre-admissibility support vector. | Add a pre_admissibility_support_vector record. |
| `admissibility.pre_vector_missing_coordinate` | The pre-admissibility vector omits a required coordinate class. | Add the missing finite coordinate to the pre-admissibility vector. |
| `admissibility.unchecked_final` | Strict finality found checked_admissibility.checked=false. | Run a checker and set checked=true only when the body/vector were checked. |
| `admissibility.unchecked_status_license` | Unchecked status cannot license admissibility. | Create a checked status body and keep admissibility inputs separate. |
| `anchor.event_free_mismatch` | An event-free root anchor is not declared event-free. | Set event_free=true or choose a different anchor kind. |
| `anchor.missing_provenance` | An observed-evidence anchor lacks provenance or reason. | Add provenance_ref or a finite reason. |
| `anchor.missing_target` | An anchor declaration points at no finite target record. | Correct target_id or add the target record. |
| `anchor.role_mismatch` | An anchor is used under a role its declaration does not permit. | Expand permitted_roles or use a role-compatible anchor. |
| `anchor.undeclared` | Strict support anchor has no typed anchor declaration. | Add anchor_declaration for every strict support anchor. |
| `certificate.cover_cycle` | A certificate cover depends on the cover it would produce. | Use independent certificate-state support before declaring cover. |
| `certificate.kernel_circular_support` | Certificate and kernel support depend on each other circularly. | Break the cycle with a prior-kernel witness or external certificate anchor. |
| `certificate.null_misuse` | A null certificate was used as if it licensed a target. | Use a real target-scoped certificate or keep the target unresolved. |
| `certificate.role_stage_violation` | Certificate use points at an incompatible validation stage. | Target the checked record or add the required checked-stage state node. |
| `certificate.support_cycle` | Certificate support is circular. | Use an acyclic certificate-state support path. |
| `compression.exactness_violation` | A compression hides a difference that changes admissibility. | Refine the compression or add a factorization that preserves the predicate. |
| `compression.factorization_missing` | A finite compression profile class lacks a usable factorization witness. | Add beta_by_value for every compressed value in the profile class. |
| `consistency.profile_incomplete` | A typed consistency profile has missing or failed coordinates. | Fill or repair the failed coordinates before using the profile. |
| `environment.policy_generation_cycle` | Environment selection and policy-generated obligation form a cycle. | Make the environment token an external input or move the generated obligation later. |
| `evidence.failure_laundering` | Failed evidence was converted into an immediate obligation. | Keep the evidence failure blocking, waive it explicitly, or add independent support. |
| `failure.filtered_blocks` | A mode-filtered failure blocks this mode. | Resolve the failure or run under a mode where it is not relevant. |
| `failure.mode_relevant_blocks` | An unresolved failure is relevant to the current mode. | Resolve it, mark it mode-irrelevant with support, or keep inadmissible. |
| `finality.missing_admissibility_body` | Strict finality lacks an admissibility_body record. | Add admissibility_body or call LedgerBuilder.finalize_checked(). |
| `finality.missing_checked_admissibility` | Strict finality lacks a checked_admissibility record. | Add checked_admissibility or call LedgerBuilder.finalize_checked(). |
| `finality.missing_checked_status` | Strict finality lacks a checked_status record. | Add checked_status or call LedgerBuilder.finalize_checked(). |
| `finality.missing_checker_or_rule_version` | A finality body lacks checker or rule version. | Record finite checker and rule version identifiers. |
| `finality.missing_pre_vector` | Strict finality lacks a pre-admissibility support vector. | Add the vector before checked_admissibility. |
| `finality.missing_read_coordinate` | A checked record omits a required read coordinate. | Add the missing read_coordinates. |
| `finality.missing_respect_coordinate` | A checked record omits a required respect coordinate. | Add the missing respect_coordinates. |
| `finality.missing_status_body` | Strict finality lacks a status_body record. | Add status_body or call LedgerBuilder.finalize_checked(). |
| `finality.output_leakage` | A final checked record reads final output as an input. | Only read pre-final bodies, support vectors, and finite witnesses. |
| `gate.cycle` | Gate requirement and gate pass support each other. | Make gate pass depend on earlier requirements only. |
| `kernel.missing_context` | The mode requires a finite validation/object kernel context. | Add kernel_admission/root_debt records or pass a Kernel object. |
| `mode.unknown` | The requested mode has no finite public contract. | Use a built-in mode or pass --allow-unknown-mode-as-draft in the CLI. |
| `obligation.discharge_cycle` | An obligation discharge depends on the discharge it would produce. | Use earlier cover/support records before marking the obligation discharged. |
| `obligation.hard_lifecycle_conflict` | A hard obligation has conflicting lifecycle records. | Choose one lifecycle transition or keep the output blocked. |
| `obligation.invalid_transition` | An obligation lifecycle transition is not allowed. | Use an allowed lifecycle transition or record a conflict. |
| `obligation.lifecycle_conflict` | One obligation has incompatible lifecycle targets in one event. | Split events or resolve the lifecycle conflict. |
| `obstruction.critical_undischarged` | A critical obstruction remains without finite discharge. | Add certificate cover, obligation discharge, or keep the ledger blocked. |
| `policy.generated_obligation_omission` | A policy gate requires an obligation that is absent. | Add the obligation record or remove the requirement with a reason. |
| `policy.self_reference` | A policy-stage record cites itself as support. | Move the support to an earlier finite record. |
| `presentation.expression_outside_scope` | A finite expression or presentation map refers outside the declared presentation. | Add the referenced items to the presentation or remove the out-of-scope refs. |
| `presentation.unmapped_distinction` | A declared finite presentation is missing a distinction-basis or map entry. | Declare the basis distinctions and map each required finite distinction. |
| `process_class.missing_registry` | A record refers to a process with no compatible process-class declaration. | Add a process_class record that admits the mode and required challenge roles. |
| `requirement.missing_empty_reason` | An empty requirement policy has no finite empty-requirement reason. | Record why the requirement set is empty. |
| `requirement.missing_reason` | A declared requirement lacks a finite reason record. | Add a RequirementReason or put a visible reason on the requirement. |
| `requirement.missing_transfer_reason` | A requirement transfer lacks a finite transfer reason. | Record why the requirement was added, removed, weakened, or transferred. |
| `requirement.unanswered_issue` | A requirement issue is not answered, pending, carried, or unresolved in the ledger. | Add the issue record and mark its finite disposition. |
| `respect.missing_coordinates` | A respect certificate omits required coordinates. | Add the missing respected coordinates or mark the certificate invalid. |
| `respect.status_admissibility_mismatch` | Admissibility does not preserve status respect coordinates. | Copy required respect coordinates into admissibility or keep inadmissible. |
| `self_modification.missing_lineage` | A self-modification transition lacks process lineage. | Add a finite lineage record or lineage_reason for the process change. |
| `self_modification.missing_rule_disclosure` | A self-modification witness does not disclose checker/rule preservation. | Declare checker_version, rule_version, and preserved/replaced/unavailable checks. |
| `settledness.license_cycle` | A settledness license depends on the licensed output it would produce. | Use lower-stage or earlier-event support for the license check. |
| `settledness.unlicensed` | A declared settled distinction lacks a checked license. | Add a non-circular license or keep the distinction as residue. |
| `stage.missing_build_record` | A strict finality record is not emitted by any stage build record. | Add a stage_build record with emitted_records and versions. |
| `stage.missing_checker_or_rule_version` | A finality stage build lacks checker or rule versions. | Record finite checker and rule versions on the stage build. |
| `stage.unfrozen_finality` | A strict finality record is in an unfrozen stage. | Call finalize/finalize_checked after appending finality records. |
| `status.missing_body` | Checked status does not point at a status_body record. | Add a status_body record and point checked_status at it. |
| `status.missing_checker_or_rule_version` | Checked status lacks checker or rule version. | Record finite checker and rule version identifiers. |
| `status.unchecked_final` | Strict finality found checked_status.checked=false. | Run a checker and set checked=true only when the body was checked. |
| `support.unavailable_evidence` | An unavailable leaf was used as finality evidence. | Use available evidence or keep the unavailable leaf as a visible blocker. |
| `transition.record_not_preserved` | A refinement transition drops records without archive or provenance. | Preserve the record, archive it explicitly, or add provenance tracing. |
| `validator.timeout` | A validator timed out and still blocks the ledger. | Rerun, waive with visible policy, or keep the output recheckable/inadmissible. |
| `validator.timeout_hidden` | A validator timeout was hidden. | Keep timeout records visible and do not pass admissibility. |

## Core Codes

The package may also return structural codes emitted directly by core validators, such as `support.cycle`, `support.missing_witness`, `certificate.missing_target`, `certificate.expired`, `kernel.self_certification`, `stage.rewrite`, `adequacy.vacuous`, and `transition.untraced_admissibility_gain`.
