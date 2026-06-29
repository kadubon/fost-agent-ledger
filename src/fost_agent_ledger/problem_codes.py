from __future__ import annotations

from dataclasses import dataclass

from .model import JsonModel


@dataclass(frozen=True)
class ProblemExplanation(JsonModel):
    code: str
    meaning: str
    likely_causes: tuple[str, ...]
    repair: str
    theory_items: tuple[str, ...] = ()


PROBLEM_EXPLANATIONS: dict[str, ProblemExplanation] = {
    "abstention.obstructed": ProblemExplanation(
        "abstention.obstructed",
        "An abstention is visible, but an obstruction prevents treating it as clean closure.",
        ("The abstention record has obstruction references.",),
        "Record the obstruction as an issue/residue or keep the ledger inadmissible.",
    ),
    "acceptance.blocked": ProblemExplanation(
        "acceptance.blocked",
        "An acceptance record says a target is accepted while blockers remain.",
        ("blocked_by is not empty.",),
        "Resolve or remove the blockers before setting accepted=true.",
    ),
    "acceptance.missing_target": ProblemExplanation(
        "acceptance.missing_target",
        "An acceptance record points at no finite ledger record.",
        ("target_id is wrong or the target record was omitted.",),
        "Add the target record or correct the target_id.",
    ),
    "admissibility.checked_status_leakage": ProblemExplanation(
        "admissibility.checked_status_leakage",
        "Admissibility used final checked status as an input.",
        ("body_record_id points at a status record.",),
        "Point admissibility at a pre-admissibility body/vector instead.",
    ),
    "admissibility.unchecked_status_license": ProblemExplanation(
        "admissibility.unchecked_status_license",
        "Unchecked status cannot license admissibility.",
        ("A status record has checked=false and is used by admissibility.",),
        "Create a checked status body and keep admissibility inputs separate.",
    ),
    "certificate.kernel_circular_support": ProblemExplanation(
        "certificate.kernel_circular_support",
        "Certificate and kernel support depend on each other circularly.",
        ("A certificate/kernel support edge is mirrored in reverse.",),
        "Break the cycle with a prior-kernel witness or external certificate anchor.",
    ),
    "certificate.null_misuse": ProblemExplanation(
        "certificate.null_misuse",
        "A null certificate was used as if it licensed a target.",
        ("A CertificateUse cites a null certificate or allowed=false.",),
        "Use a real target-scoped certificate or keep the target unresolved.",
        ("D056",),
    ),
    "certificate.cover_cycle": ProblemExplanation(
        "certificate.cover_cycle",
        "A certificate cover depends on the cover it would produce.",
        ("CertificateCover.support_refs contains the cover record itself.",),
        "Use independent certificate-state support before declaring cover.",
        ("D069", "R026"),
    ),
    "certificate.role_stage_violation": ProblemExplanation(
        "certificate.role_stage_violation",
        "Certificate use points at an incompatible validation stage.",
        ("A certificate target points at a candidate-stage record.",),
        "Target the checked record or add the required checked-stage state node.",
    ),
    "certificate.support_cycle": ProblemExplanation(
        "certificate.support_cycle",
        "Certificate support is circular.",
        ("Certificate support edges point back to their own support.",),
        "Use an acyclic certificate-state support path.",
    ),
    "consistency.profile_incomplete": ProblemExplanation(
        "consistency.profile_incomplete",
        "A typed consistency profile has missing or failed coordinates.",
        ("passed=false, missing_coordinates, or failed_coordinates are present.",),
        "Fill or repair the failed coordinates before using the profile.",
    ),
    "compression.exactness_violation": ProblemExplanation(
        "compression.exactness_violation",
        "A compression hides a difference that changes admissibility.",
        ("Two profiles share one compressed value but have different admissibility.",),
        "Refine the compression or add a factorization that preserves the predicate.",
        ("C002", "C003", "R052"),
    ),
    "compression.factorization_missing": ProblemExplanation(
        "compression.factorization_missing",
        "A finite compression profile class lacks a usable factorization witness.",
        ("No CompressionFactorization record exists or beta omits compressed values.",),
        "Add beta_by_value for every compressed value in the profile class.",
        ("C003",),
    ),
    "environment.policy_generation_cycle": ProblemExplanation(
        "environment.policy_generation_cycle",
        "Environment selection and policy-generated obligation form a cycle.",
        ("Support edges connect an environment token and obligation both ways.",),
        "Make the environment token an external input or move the generated obligation later.",
    ),
    "evidence.failure_laundering": ProblemExplanation(
        "evidence.failure_laundering",
        "Failed evidence was converted into an immediate obligation.",
        ("An obligation cites failed evidence as support.",),
        "Keep the evidence failure blocking, waive it explicitly, or add independent support.",
    ),
    "failure.filtered_blocks": ProblemExplanation(
        "failure.filtered_blocks",
        "A mode-filtered failure blocks this mode.",
        ("ModeFilteredFailure.blocks is true for the current mode.",),
        "Resolve the failure or run under a mode where it is not relevant.",
    ),
    "failure.mode_relevant_blocks": ProblemExplanation(
        "failure.mode_relevant_blocks",
        "An unresolved failure is relevant to the current mode.",
        ("Failure is relevant, blocking, and unresolved.",),
        "Resolve it, mark it mode-irrelevant with support, or keep inadmissible.",
    ),
    "obligation.discharge_cycle": ProblemExplanation(
        "obligation.discharge_cycle",
        "An obligation discharge depends on the discharge it would produce.",
        ("ObligationDischarge.support_refs or its cover support points back to the discharge.",),
        "Use earlier cover/support records before marking the obligation discharged.",
        ("D069", "R026"),
    ),
    "finality.output_leakage": ProblemExplanation(
        "finality.output_leakage",
        "A final checked record reads final output as an input.",
        ("reads_final_output is set on status/admissibility.",),
        "Only read pre-final bodies, support vectors, and finite witnesses.",
    ),
    "gate.cycle": ProblemExplanation(
        "gate.cycle",
        "Gate requirement and gate pass support each other.",
        ("Support graph contains both requirement->pass and pass->requirement.",),
        "Make gate pass depend on earlier requirements only.",
    ),
    "obligation.hard_lifecycle_conflict": ProblemExplanation(
        "obligation.hard_lifecycle_conflict",
        "A hard obligation has conflicting lifecycle records.",
        ("Multiple lifecycle targets exist for one obligation/event.",),
        "Choose one lifecycle transition or keep the output blocked.",
    ),
    "obligation.invalid_transition": ProblemExplanation(
        "obligation.invalid_transition",
        "An obligation lifecycle transition is not allowed.",
        ("source->target is not in the finite lifecycle automaton.",),
        "Use an allowed lifecycle transition or record a conflict.",
    ),
    "obligation.lifecycle_conflict": ProblemExplanation(
        "obligation.lifecycle_conflict",
        "One obligation has incompatible lifecycle targets in one event.",
        ("Two lifecycle records disagree for the same obligation/event.",),
        "Split events or resolve the lifecycle conflict.",
    ),
    "policy.generated_obligation_omission": ProblemExplanation(
        "policy.generated_obligation_omission",
        "A policy gate requires an obligation that is absent.",
        ("required_obligations names an obligation not in the ledger.",),
        "Add the obligation record or remove the requirement with a reason.",
    ),
    "policy.self_reference": ProblemExplanation(
        "policy.self_reference",
        "A policy-stage record cites itself as support.",
        ("support_refs or support graph contains self-reference.",),
        "Move the support to an earlier finite record.",
    ),
    "presentation.expression_outside_scope": ProblemExplanation(
        "presentation.expression_outside_scope",
        "A finite expression or presentation map refers outside the declared presentation.",
        ("Expression refs or presentation map target records are not in scope.",),
        "Add the referenced items to the presentation or remove the out-of-scope refs.",
        ("D028", "D029", "D030"),
    ),
    "presentation.unmapped_distinction": ProblemExplanation(
        "presentation.unmapped_distinction",
        "A declared finite presentation is missing a distinction-basis or map entry.",
        ("A presentation uses undeclared distinctions or a total map omits them.",),
        "Declare the basis distinctions and map each required finite distinction.",
        ("D027", "D028", "D029"),
    ),
    "process_class.missing_registry": ProblemExplanation(
        "process_class.missing_registry",
        "A record refers to a process with no compatible process-class declaration.",
        ("Requirement policy or metadata names a process not in the registry.",),
        "Add a process_class record that admits the mode and required challenge roles.",
        ("D026",),
    ),
    "requirement.missing_empty_reason": ProblemExplanation(
        "requirement.missing_empty_reason",
        "An empty requirement policy has no finite empty-requirement reason.",
        ("RequirementPolicy has no requirements and no reason.",),
        "Record why the requirement set is empty.",
        ("D045", "D048"),
    ),
    "requirement.missing_reason": ProblemExplanation(
        "requirement.missing_reason",
        "A declared requirement lacks a finite reason record.",
        ("RequirementPolicy names a requirement with no reason text or RequirementReason.",),
        "Add a RequirementReason or put a visible reason on the requirement.",
        ("D045", "D048"),
    ),
    "requirement.missing_transfer_reason": ProblemExplanation(
        "requirement.missing_transfer_reason",
        "A requirement transfer lacks a finite transfer reason.",
        ("RequirementTransfer.reason is empty.",),
        "Record why the requirement was added, removed, weakened, or transferred.",
        ("D045", "D048"),
    ),
    "requirement.unanswered_issue": ProblemExplanation(
        "requirement.unanswered_issue",
        "A requirement issue is not answered, pending, carried, or unresolved in the ledger.",
        ("RequirementPolicy.issue_ids points at a missing or undisposed issue.",),
        "Add the issue record and mark its finite disposition.",
        ("D046", "D048"),
    ),
    "respect.missing_coordinates": ProblemExplanation(
        "respect.missing_coordinates",
        "A respect certificate omits required coordinates.",
        ("required_coordinates is not covered by respected_coordinates.",),
        "Add the missing respected coordinates or mark the certificate invalid.",
    ),
    "respect.status_admissibility_mismatch": ProblemExplanation(
        "respect.status_admissibility_mismatch",
        "Admissibility does not preserve status respect coordinates.",
        ("Status and admissibility respect coordinate sets differ.",),
        "Copy required respect coordinates into admissibility or keep inadmissible.",
    ),
    "self_modification.missing_lineage": ProblemExplanation(
        "self_modification.missing_lineage",
        "A self-modification transition lacks process lineage.",
        ("No SelfModificationWitness exists or it has no lineage record/reason.",),
        "Add a finite lineage record or lineage_reason for the process change.",
        ("D093",),
    ),
    "self_modification.missing_rule_disclosure": ProblemExplanation(
        "self_modification.missing_rule_disclosure",
        "A self-modification witness does not disclose checker/rule preservation.",
        ("Checker version, rule version, or required check disposition is missing.",),
        "Declare checker_version, rule_version, and preserved/replaced/unavailable checks.",
        ("D093",),
    ),
    "settledness.license_cycle": ProblemExplanation(
        "settledness.license_cycle",
        "A settledness license depends on the licensed output it would produce.",
        ("The license cites itself or has circular support.",),
        "Use lower-stage or earlier-event support for the license check.",
        ("D049", "R025"),
    ),
    "settledness.unlicensed": ProblemExplanation(
        "settledness.unlicensed",
        "A declared settled distinction lacks a checked license.",
        ("SettlednessDeclaration has no matching licensed SettlednessLicense.",),
        "Add a non-circular license or keep the distinction as residue.",
        ("D049",),
    ),
    "obstruction.critical_undischarged": ProblemExplanation(
        "obstruction.critical_undischarged",
        "A critical obstruction remains without finite discharge.",
        ("ObstructionProfile or critical Obstruction lacks cover/discharge.",),
        "Add certificate cover, obligation discharge, or keep the ledger blocked.",
        ("D053", "D069"),
    ),
    "transition.record_not_preserved": ProblemExplanation(
        "transition.record_not_preserved",
        "A refinement transition drops records without archive or provenance.",
        ("RecordPreservingRefinement omits a before_record_id.",),
        "Preserve the record, archive it explicitly, or add provenance tracing.",
        ("D092",),
    ),
    "validator.timeout": ProblemExplanation(
        "validator.timeout",
        "A validator timed out and still blocks the ledger.",
        ("ValidatorTimeout.blocks is true.",),
        "Rerun, waive with visible policy, or keep the output recheckable/inadmissible.",
    ),
    "validator.timeout_hidden": ProblemExplanation(
        "validator.timeout_hidden",
        "A validator timeout was hidden.",
        ("ValidatorTimeout.hidden is true.",),
        "Keep timeout records visible and do not pass admissibility.",
    ),
}


def explain_problem(code: str) -> ProblemExplanation | None:
    return PROBLEM_EXPLANATIONS.get(code)
