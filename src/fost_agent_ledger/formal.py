from __future__ import annotations

from collections import defaultdict

from .enums import CertificateUseKind, LedgerStage, ProblemSeverity, RecordType
from .ledger import EvaluatedLedger
from .model import LedgerRecord, Problem
from .modes import ModeContract
from .obligations import ObligationLifecycleRecord, validate_lifecycle_record


def _string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple, set, frozenset)):
        return tuple(str(item) for item in value)
    if isinstance(value, str):
        return (value,)
    return ()


def validate_formal_completion(
    ledger: EvaluatedLedger, contract: ModeContract
) -> tuple[Problem, ...]:
    """Validate finite countermodel cases that span multiple typed record families."""

    records = {record.id: record for record in ledger.records}
    problems: list[Problem] = []
    problems.extend(_validate_policy_self_reference(ledger))
    problems.extend(_validate_lifecycle_records(ledger))
    problems.extend(_validate_acceptance_and_abstention(ledger, records))
    problems.extend(_validate_failure_filtering(ledger, contract))
    problems.extend(_validate_consistency_profiles(ledger))
    problems.extend(_validate_validator_timeouts(ledger))
    problems.extend(_validate_null_certificates(ledger))
    problems.extend(_validate_respect_certificates(ledger))
    problems.extend(_validate_finality_strengthening(ledger, records))
    problems.extend(_validate_gate_and_policy_cycles(ledger, records))
    problems.extend(_validate_certificate_support_strengthening(ledger, records))
    problems.extend(_validate_evidence_failure_laundering(ledger))
    problems.extend(_validate_process_classes(ledger, contract))
    problems.extend(_validate_presentations(ledger, records))
    problems.extend(_validate_requirement_policies(ledger, records))
    problems.extend(_validate_settledness(ledger))
    problems.extend(_validate_obstruction_cover_and_discharge(ledger))
    problems.extend(_validate_record_preserving_refinement(ledger))
    problems.extend(_validate_self_modification(ledger, contract))
    problems.extend(_validate_compression_witnesses(ledger))
    return tuple(problems)


def _validate_policy_self_reference(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    for record in ledger.by_stage(LedgerStage.CHECKED_POLICY):
        if record.id in record.support_refs:
            problems.append(
                Problem(
                    code="policy.self_reference",
                    message="policy-stage record cannot cite itself as support",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id,),
                )
            )
    for edge in ledger.support_graph.edges:
        source = ledger.support_graph.nodes.get(edge.source_id)
        target = ledger.support_graph.nodes.get(edge.target_id)
        if (
            source is not None
            and target is not None
            and source.stage == LedgerStage.CHECKED_POLICY
            and target.stage == LedgerStage.CHECKED_POLICY
            and edge.source_id == edge.target_id
        ):
            problems.append(
                Problem(
                    code="policy.self_reference",
                    message="policy support graph contains a self-reference",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(edge.source_id,),
                )
            )
    return tuple(problems)


def _validate_lifecycle_records(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    by_obligation_event: dict[tuple[str, str], set[str]] = defaultdict(set)
    hard_obligations = {
        str(record.payload.get("obligation_id", record.id))
        for record in ledger.find(RecordType.OBLIGATION)
        if bool(record.payload.get("hard", False))
    }
    for record in ledger.find(RecordType.OBLIGATION_LIFECYCLE):
        lifecycle = ObligationLifecycleRecord.from_dict(
            {
                "record_id": record.id,
                "obligation_id": record.payload.get("obligation_id", ""),
                "source": record.payload.get("source", "undeclared"),
                "target": record.payload.get("target", "declared"),
                "event_id": record.payload.get("event_id", record.event_id),
                "deadline_status": record.payload.get("deadline_status", "not_applicable"),
                "reason": record.payload.get("reason", ""),
            }
        )
        problems.extend(validate_lifecycle_record(lifecycle))
        key = (lifecycle.obligation_id, lifecycle.event_id)
        by_obligation_event[key].add(lifecycle.target.value)
    for (obligation_id, event_id), targets in by_obligation_event.items():
        if len(targets) <= 1:
            continue
        problems.append(
            Problem(
                code="obligation.lifecycle_conflict",
                message="same obligation has incompatible lifecycle targets in one event",
                severity=ProblemSeverity.ERROR,
                related_record_ids=(obligation_id, event_id),
            )
        )
        if obligation_id in hard_obligations:
            problems.append(
                Problem(
                    code="obligation.hard_lifecycle_conflict",
                    message="hard obligation has conflicting lifecycle records",
                    severity=ProblemSeverity.BLOCKER,
                    related_record_ids=(obligation_id, event_id),
                )
            )
    return tuple(problems)


def _validate_acceptance_and_abstention(
    ledger: EvaluatedLedger, records: dict[str, LedgerRecord]
) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    for record in ledger.find(RecordType.ACCEPTANCE):
        target_id = str(record.payload.get("target_id", ""))
        if target_id not in records:
            problems.append(
                Problem(
                    code="acceptance.missing_target",
                    message="acceptance record points at no finite target record",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id, target_id),
                )
            )
        if bool(record.payload.get("accepted", False)) and _string_tuple(
            record.payload.get("blocked_by")
        ):
            problems.append(
                Problem(
                    code="acceptance.blocked",
                    message="accepted target still has blocking acceptance edges",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id, target_id),
                )
            )
    for record in ledger.find(RecordType.ABSTENTION):
        if bool(record.payload.get("abstained", True)) and (
            bool(record.payload.get("obstructed", False))
            or bool(_string_tuple(record.payload.get("obstruction_refs")))
        ):
            problems.append(
                Problem(
                    code="abstention.obstructed",
                    message="abstention is obstructed and cannot be treated as clean closure",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id,),
                )
            )
    return tuple(problems)


def _validate_failure_filtering(
    ledger: EvaluatedLedger, contract: ModeContract
) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    for record in ledger.find(RecordType.FAILURE):
        mode = str(record.payload.get("mode", ""))
        relevant = bool(record.payload.get("relevant", True))
        blocking = bool(record.payload.get("blocking", True))
        resolved = bool(record.payload.get("resolved", False))
        mode_relevant = mode in {"", ledger.mode, contract.name}
        if relevant and mode_relevant and blocking and not resolved:
            problems.append(
                Problem(
                    code="failure.mode_relevant_blocks",
                    message="mode-relevant unresolved failure blocks admissibility",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id,),
                )
            )
    for record in ledger.find(RecordType.MODE_FILTERED_FAILURE):
        mode = str(record.payload.get("mode", ""))
        if mode in {ledger.mode, contract.name} and bool(record.payload.get("blocks", False)):
            problems.append(
                Problem(
                    code="failure.filtered_blocks",
                    message="mode-filtered failure blocks this mode",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id,),
                )
            )
    return tuple(problems)


def _validate_consistency_profiles(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    for record in ledger.find(RecordType.CONSISTENCY_PROFILE):
        missing = _string_tuple(record.payload.get("missing_coordinates"))
        failed = _string_tuple(record.payload.get("failed_coordinates"))
        if not bool(record.payload.get("passed", True)) or missing or failed:
            problems.append(
                Problem(
                    code="consistency.profile_incomplete",
                    message="typed consistency profile has missing or failed coordinates",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id, *missing, *failed),
                )
            )
    return tuple(problems)


def _validate_validator_timeouts(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    for record in ledger.find(RecordType.VALIDATOR_TIMEOUT):
        if bool(record.payload.get("hidden", False)):
            problems.append(
                Problem(
                    code="validator.timeout_hidden",
                    message="validator timeout cannot be hidden",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id,),
                )
            )
        if bool(record.payload.get("blocks", True)):
            problems.append(
                Problem(
                    code="validator.timeout",
                    message="blocking validator timeout remains visible",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id,),
                )
            )
    return tuple(problems)


def _validate_null_certificates(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    null_certificate_ids = {
        str(record.payload.get("certificate_id", record.id))
        for record in ledger.find(RecordType.NULL_CERTIFICATE)
        if not bool(record.payload.get("allowed", False))
    }
    for record in ledger.find(RecordType.NULL_CERTIFICATE):
        if not bool(record.payload.get("allowed", False)):
            problems.append(
                Problem(
                    code="certificate.null_misuse",
                    message="null certificate cannot license a target",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id, str(record.payload.get("target_id", ""))),
                )
            )
    for use in ledger.find(RecordType.CERTIFICATE_USE):
        certificate_id = str(use.payload.get("certificate_id", ""))
        if certificate_id in null_certificate_ids:
            problems.append(
                Problem(
                    code="certificate.null_misuse",
                    message="certificate use cites a null certificate",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(use.id, certificate_id),
                )
            )
    return tuple(problems)


def _validate_respect_certificates(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    for record in ledger.find(RecordType.RESPECT_CERTIFICATE):
        required = set(_string_tuple(record.payload.get("required_coordinates")))
        respected = set(_string_tuple(record.payload.get("respected_coordinates")))
        if not bool(record.payload.get("valid", True)):
            problems.append(
                Problem(
                    code="respect.certificate_invalid",
                    message="respect certificate is explicitly invalid",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id,),
                )
            )
        missing = tuple(sorted(required - respected))
        if missing:
            problems.append(
                Problem(
                    code="respect.missing_coordinates",
                    message="respect certificate omits required coordinates",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id, *missing),
                )
            )
    return tuple(problems)


def _validate_finality_strengthening(
    ledger: EvaluatedLedger, records: dict[str, LedgerRecord]
) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    status_respect: set[str] = set()
    admissibility_respect: set[str] = set()
    for record in ledger.find(RecordType.STATUS):
        status_respect.update(_string_tuple(record.payload.get("respect_coordinates")))
        if bool(record.payload.get("reads_final_output", False)) or bool(
            record.metadata.get("reads_final_output", False)
        ):
            problems.append(
                Problem(
                    code="finality.output_leakage",
                    message="checked status cannot read final output as an input",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id,),
                )
            )
    for record in ledger.find(RecordType.ADMISSIBILITY):
        admissibility_respect.update(_string_tuple(record.payload.get("respect_coordinates")))
        body_id = record.payload.get("body_record_id")
        body_record = records.get(str(body_id)) if body_id is not None else None
        if (
            body_record is not None
            and body_record.record_type == RecordType.STATUS
            and not bool(body_record.payload.get("checked", True))
        ):
            problems.append(
                Problem(
                    code="admissibility.unchecked_status_license",
                    message="unchecked status cannot license admissibility",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id, body_record.id),
                )
            )
        if bool(record.payload.get("reads_final_output", False)) or bool(
            record.metadata.get("reads_final_output", False)
        ):
            problems.append(
                Problem(
                    code="finality.output_leakage",
                    message="checked admissibility cannot read final output as an input",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id,),
                )
            )
    missing_respect = tuple(sorted(status_respect - admissibility_respect))
    if status_respect and missing_respect:
        problems.append(
            Problem(
                code="respect.status_admissibility_mismatch",
                message="status respect coordinates are not preserved by admissibility",
                severity=ProblemSeverity.ERROR,
                related_record_ids=missing_respect,
            )
        )
    return tuple(problems)


def _validate_gate_and_policy_cycles(
    ledger: EvaluatedLedger, records: dict[str, LedgerRecord]
) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    edges = {(edge.source_id, edge.target_id) for edge in ledger.support_graph.edges}
    for gate_req in ledger.find(RecordType.GATE_REQUIREMENT):
        required_obligations = set(_string_tuple(gate_req.payload.get("required_obligations")))
        obligation_ids = {
            str(record.payload.get("obligation_id", record.id))
            for record in ledger.find(RecordType.OBLIGATION)
        }
        missing = tuple(sorted(required_obligations - obligation_ids))
        if missing:
            problems.append(
                Problem(
                    code="policy.generated_obligation_omission",
                    message="gate requirement names obligations that are not present",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(gate_req.id, *missing),
                )
            )
        for gate_pass in ledger.find(RecordType.GATE_PASS):
            if (gate_req.id, gate_pass.id) in edges and (gate_pass.id, gate_req.id) in edges:
                problems.append(
                    Problem(
                        code="gate.cycle",
                        message="gate requirement and gate pass support each other circularly",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(gate_req.id, gate_pass.id),
                    )
                )
    for env in ledger.find(RecordType.ENVIRONMENT_TOKEN):
        for obligation in ledger.find(RecordType.OBLIGATION):
            if (env.id, obligation.id) in edges and (obligation.id, env.id) in edges:
                problems.append(
                    Problem(
                        code="environment.policy_generation_cycle",
                        message="environment token and policy obligation form a generation cycle",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(env.id, obligation.id),
                    )
                )
    return tuple(problems)


def _validate_certificate_support_strengthening(
    ledger: EvaluatedLedger, records: dict[str, LedgerRecord]
) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    edges = {(edge.source_id, edge.target_id, edge.role) for edge in ledger.support_graph.edges}
    for source_id, target_id, _role in edges:
        source = records.get(source_id)
        target = records.get(target_id)
        if source is None or target is None:
            continue
        source_cert_or_kernel = source.record_type in {
            RecordType.CERTIFICATE,
            RecordType.CERTIFICATE_STATE,
            RecordType.KERNEL_ADMISSION,
        }
        target_cert_or_kernel = target.record_type in {
            RecordType.CERTIFICATE,
            RecordType.CERTIFICATE_STATE,
            RecordType.KERNEL_ADMISSION,
        }
        if (
            source_cert_or_kernel
            and target_cert_or_kernel
            and (
                target_id,
                source_id,
                _role,
            )
            in edges
        ):
            problems.append(
                Problem(
                    code="certificate.kernel_circular_support",
                    message="certificate/kernel support cannot be circular",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(source_id, target_id),
                )
            )
        if (
            source.record_type in {RecordType.CERTIFICATE, RecordType.CERTIFICATE_STATE}
            and (
                target_id,
                source_id,
                _role,
            )
            in edges
        ):
            problems.append(
                Problem(
                    code="certificate.support_cycle",
                    message="certificate support cycle blocks validation",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(source_id, target_id),
                )
            )
    for target in ledger.find(RecordType.CERTIFICATE_TARGET):
        target_node = str(target.payload.get("target_node", ""))
        target_record = records.get(target_node)
        if target_record is None:
            continue
        if target_record.stage == LedgerStage.CANDIDATE:
            problems.append(
                Problem(
                    code="certificate.role_stage_violation",
                    message="certificate target points at a pre-policy candidate stage",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(target.id, target_node),
                )
            )
        if (
            target.payload.get("use_kind") == CertificateUseKind.COVER.value
            and target_record.record_type == RecordType.OBLIGATION
            and target_record.payload.get("lifecycle") == "discharged"
        ):
            problems.append(
                Problem(
                    code="certificate.cover_check_type_confusion",
                    message="cover certificate cannot discharge an obligation by type confusion",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(target.id, target_node),
                )
            )
    return tuple(problems)


def _validate_evidence_failure_laundering(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    failed_evidence = {
        record.id
        for record in ledger.find(RecordType.EVIDENCE)
        if record.payload.get("state") in {"fail", "conflict", "timeout"}
        or record.payload.get("disposition") in {"blocked", "conflict"}
    }
    problems: list[Problem] = []
    for obligation in ledger.find(RecordType.OBLIGATION):
        support_refs = set(_string_tuple(obligation.payload.get("support_refs")))
        laundered = tuple(sorted(failed_evidence & support_refs))
        if laundered:
            problems.append(
                Problem(
                    code="evidence.failure_laundering",
                    message="failed evidence cannot be laundered by an immediate obligation",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(obligation.id, *laundered),
                )
            )
    return tuple(problems)


def _validate_process_classes(
    ledger: EvaluatedLedger, contract: ModeContract
) -> tuple[Problem, ...]:
    process_records = {
        str(record.payload.get("process_id", record.id)): record
        for record in ledger.find(RecordType.PROCESS_CLASS)
    }
    required_process_ids = {
        str(record.payload.get("process_id", ""))
        for record_type in (RecordType.REQUIREMENT_POLICY,)
        for record in ledger.find(record_type)
        if str(record.payload.get("process_id", ""))
    }
    metadata_process = ledger.metadata.get("process_id")
    if isinstance(metadata_process, str) and ledger.metadata.get("process_class_required", False):
        required_process_ids.add(metadata_process)
    problems: list[Problem] = []
    for process_id in sorted(required_process_ids):
        record = process_records.get(process_id)
        if record is None:
            problems.append(
                Problem(
                    code="process_class.missing_registry",
                    message="record refers to a process with no declared process-class registry",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(process_id,),
                )
            )
            continue
        modes = set(_string_tuple(record.payload.get("modes")))
        if modes and "*" not in modes and ledger.mode not in modes and contract.name not in modes:
            problems.append(
                Problem(
                    code="process_class.missing_registry",
                    message="process-class registry does not admit this mode",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id, ledger.mode),
                )
            )
        roles = set(_string_tuple(record.payload.get("challenge_roles")))
        missing_roles = tuple(sorted(set(contract.critic_role_requirements) - roles))
        if contract.critic_role_requirements and roles and missing_roles:
            problems.append(
                Problem(
                    code="process_class.missing_registry",
                    message="process-class registry omits required challenge roles",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id, *missing_roles),
                )
            )
    return tuple(problems)


def _validate_presentations(
    ledger: EvaluatedLedger, records: dict[str, LedgerRecord]
) -> tuple[Problem, ...]:
    basis_by_id = {
        str(record.payload.get("basis_id", record.id)): record
        for record in ledger.find(RecordType.DISTINCTION_BASIS)
    }
    presentation_by_id = {
        str(record.payload.get("presentation_id", record.id)): record
        for record in ledger.find(RecordType.FINITE_PRESENTATION)
    }
    expression_by_id = {
        str(record.payload.get("expression_id", record.id)): record
        for record in ledger.find(RecordType.FINITE_EXPRESSION)
    }
    problems: list[Problem] = []
    for presentation in presentation_by_id.values():
        basis_id = str(presentation.payload.get("basis_id", ""))
        basis = basis_by_id.get(basis_id)
        distinctions = set(_string_tuple(presentation.payload.get("distinction_ids")))
        if basis is None:
            problems.append(
                Problem(
                    code="presentation.unmapped_distinction",
                    message="finite presentation names no declared distinction basis",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(presentation.id, basis_id),
                )
            )
        else:
            declared = set(_string_tuple(basis.payload.get("distinctions")))
            missing = tuple(sorted(distinctions - declared))
            if missing:
                problems.append(
                    Problem(
                        code="presentation.unmapped_distinction",
                        message="finite presentation uses distinctions outside its basis",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(presentation.id, *missing),
                    )
                )
        expression_id = presentation.payload.get("expression_id")
        if expression_id and str(expression_id) not in expression_by_id:
            problems.append(
                Problem(
                    code="presentation.expression_outside_scope",
                    message="finite presentation points at no finite expression record",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(presentation.id, str(expression_id)),
                )
            )
    for mapping in ledger.find(RecordType.PRESENTATION_MAP):
        presentation_id = str(mapping.payload.get("presentation_id", ""))
        mapping_presentation = presentation_by_id.get(presentation_id)
        if mapping_presentation is None:
            problems.append(
                Problem(
                    code="presentation.unmapped_distinction",
                    message="presentation map points at no finite presentation",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(mapping.id, presentation_id),
                )
            )
            continue
        if bool(mapping.payload.get("total", True)):
            required = set(_string_tuple(mapping_presentation.payload.get("distinction_ids")))
            mapped = set(_string_tuple(mapping.payload.get("domain_distinctions"))) | set(
                _string_tuple(mapping.payload.get("mapped_distinctions"))
            )
            missing = tuple(sorted(required - mapped))
            if missing:
                problems.append(
                    Problem(
                        code="presentation.unmapped_distinction",
                        message="presentation map is declared total but omits distinctions",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(mapping.id, *missing),
                    )
                )
        missing_targets = tuple(
            target
            for target in _string_tuple(mapping.payload.get("target_records"))
            if target not in records
        )
        if missing_targets:
            problems.append(
                Problem(
                    code="presentation.expression_outside_scope",
                    message="presentation map targets records outside this ledger",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(mapping.id, *missing_targets),
                )
            )
    for expression in expression_by_id.values():
        presentation_id_raw = expression.payload.get("presentation_id")
        if presentation_id_raw is None:
            continue
        presentation_id = str(presentation_id_raw)
        expression_presentation = presentation_by_id.get(presentation_id)
        if expression_presentation is None:
            problems.append(
                Problem(
                    code="presentation.expression_outside_scope",
                    message="finite expression names no finite presentation",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(expression.id, presentation_id),
                )
            )
            continue
        allowed_distinctions = set(
            _string_tuple(expression_presentation.payload.get("distinction_ids"))
        )
        distinction_refs = set(_string_tuple(expression.payload.get("distinction_refs")))
        outside_distinctions = tuple(sorted(distinction_refs - allowed_distinctions))
        allowed_records = set(_string_tuple(expression_presentation.payload.get("record_ids")))
        record_refs = set(_string_tuple(expression.payload.get("record_refs")))
        outside_records = tuple(sorted(record_refs - allowed_records - {expression.id}))
        if outside_distinctions or outside_records:
            problems.append(
                Problem(
                    code="presentation.expression_outside_scope",
                    message="finite expression refers outside its presentation scope",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(expression.id, *outside_distinctions, *outside_records),
                )
            )
    return tuple(problems)


def _validate_requirement_policies(
    ledger: EvaluatedLedger, records: dict[str, LedgerRecord]
) -> tuple[Problem, ...]:
    requirement_records = {record.id: record for record in ledger.find(RecordType.REQUIREMENT)} | {
        str(record.payload.get("requirement_id", "")): record
        for record in ledger.find(RecordType.REQUIREMENT)
        if str(record.payload.get("requirement_id", ""))
    }
    reason_records = {
        str(record.payload.get("requirement_id", "")): record
        for record in ledger.find(RecordType.REQUIREMENT_REASON)
    }
    problems: list[Problem] = []
    for policy in ledger.find(RecordType.REQUIREMENT_POLICY):
        requirements = _string_tuple(policy.payload.get("requirements"))
        if not requirements or bool(policy.payload.get("empty", False)):
            has_empty_reason = bool(str(policy.payload.get("reason", "")).strip()) or (
                "__empty__" in reason_records
            )
            if not has_empty_reason:
                problems.append(
                    Problem(
                        code="requirement.missing_empty_reason",
                        message="empty requirement policy needs a finite empty-requirement reason",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(policy.id,),
                    )
                )
        for requirement_id in requirements:
            requirement = requirement_records.get(requirement_id)
            if requirement is None:
                problems.append(
                    Problem(
                        code="requirement.missing_reason",
                        message="requirement policy names no finite requirement record",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(policy.id, requirement_id),
                    )
                )
                continue
            has_reason = bool(str(requirement.payload.get("reason", "")).strip()) or (
                requirement_id in reason_records
                and bool(str(reason_records[requirement_id].payload.get("reason", "")).strip())
            )
            if not has_reason:
                problems.append(
                    Problem(
                        code="requirement.missing_reason",
                        message="declared requirement lacks a finite reason record",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(policy.id, requirement.id),
                    )
                )
        for issue_id in _string_tuple(policy.payload.get("issue_ids")):
            issue = records.get(issue_id)
            if issue is None or issue.record_type != RecordType.ISSUE:
                problems.append(
                    Problem(
                        code="requirement.unanswered_issue",
                        message="requirement policy names no finite issue record",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(policy.id, issue_id),
                    )
                )
                continue
            disposition = str(
                issue.payload.get("disposition", issue.metadata.get("disposition", ""))
            )
            answered = bool(issue.payload.get("resolved", False)) or disposition in {
                "answered",
                "pending",
                "carried",
                "unresolved",
            }
            if not answered:
                problems.append(
                    Problem(
                        code="requirement.unanswered_issue",
                        message=(
                            "requirement issue is neither answered, pending, "
                            "carried, nor unresolved"
                        ),
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(policy.id, issue.id),
                    )
                )
    for transfer in ledger.find(RecordType.REQUIREMENT_TRANSFER):
        if not str(transfer.payload.get("reason", "")).strip():
            problems.append(
                Problem(
                    code="requirement.missing_transfer_reason",
                    message="requirement transfer lacks a finite transfer reason",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(
                        transfer.id,
                        str(transfer.payload.get("requirement_id", "")),
                    ),
                )
            )
    return tuple(problems)


def _validate_settledness(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    licenses_by_distinction: dict[str, list[LedgerRecord]] = defaultdict(list)
    problems: list[Problem] = []
    for license_record in ledger.find(RecordType.SETTLEDNESS_LICENSE):
        distinction_id = str(license_record.payload.get("distinction_id", ""))
        licenses_by_distinction[distinction_id].append(license_record)
        support_refs = set(_string_tuple(license_record.payload.get("support_refs"))) | set(
            license_record.support_refs
        )
        checker_record_id = str(license_record.payload.get("checker_record_id", ""))
        if license_record.id in support_refs or checker_record_id == license_record.id:
            problems.append(
                Problem(
                    code="settledness.license_cycle",
                    message="settledness license depends on the licensed output it produces",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(license_record.id, distinction_id),
                )
            )
    edges = {(edge.source_id, edge.target_id) for edge in ledger.support_graph.edges}
    for source_id, target_id in edges:
        if (target_id, source_id) not in edges:
            continue
        license_records = ledger.find(RecordType.SETTLEDNESS_LICENSE)
        source_is_license = any(record.id == source_id for record in license_records)
        target_is_license = any(record.id == target_id for record in license_records)
        if source_is_license or target_is_license:
            problems.append(
                Problem(
                    code="settledness.license_cycle",
                    message="settledness license support is circular",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(source_id, target_id),
                )
            )
    for declaration in ledger.find(RecordType.SETTLEDNESS_DECLARATION):
        distinction_id = str(declaration.payload.get("distinction_id", ""))
        licenses = licenses_by_distinction.get(distinction_id, [])
        if not any(bool(record.payload.get("licensed", True)) for record in licenses):
            problems.append(
                Problem(
                    code="settledness.unlicensed",
                    message="declared settled distinction has no checked settledness license",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(declaration.id, distinction_id),
                )
            )
    return tuple(problems)


def _validate_obstruction_cover_and_discharge(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    discharged_obstructions: set[str] = set()
    cover_by_id: dict[str, LedgerRecord] = {}
    problems: list[Problem] = []
    for cover in ledger.find(RecordType.CERTIFICATE_COVER):
        cover_id = str(cover.payload.get("cover_id", cover.id))
        cover_by_id[cover_id] = cover
        support_refs = set(_string_tuple(cover.payload.get("support_refs"))) | set(
            cover.support_refs
        )
        if cover.id in support_refs or cover_id in support_refs:
            problems.append(
                Problem(
                    code="certificate.cover_cycle",
                    message="certificate cover depends on the cover it would produce",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(cover.id, str(cover.payload.get("obstruction_id", ""))),
                )
            )
        if bool(cover.payload.get("discharged", False)):
            discharged_obstructions.add(str(cover.payload.get("obstruction_id", "")))
    for discharge in ledger.find(RecordType.OBLIGATION_DISCHARGE):
        discharge_id = str(discharge.payload.get("discharge_id", discharge.id))
        support_refs = set(_string_tuple(discharge.payload.get("support_refs"))) | set(
            discharge.support_refs
        )
        cover_id = str(discharge.payload.get("certificate_cover_id", ""))
        cover_record = cover_by_id.get(cover_id)
        cover_support = (
            set(_string_tuple(cover_record.payload.get("support_refs")))
            | set(cover_record.support_refs)
            if cover_record is not None
            else set()
        )
        if (
            discharge.id in support_refs
            or discharge_id in support_refs
            or discharge.id in cover_support
        ):
            problems.append(
                Problem(
                    code="obligation.discharge_cycle",
                    message="obligation discharge depends on the discharge it would produce",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(discharge.id, cover_id),
                )
            )
        if bool(discharge.payload.get("discharged", True)):
            obstruction_id = str(discharge.payload.get("obstruction_id", ""))
            if obstruction_id:
                discharged_obstructions.add(obstruction_id)
    for profile in ledger.find(RecordType.OBSTRUCTION_PROFILE):
        discharged_obstructions.update(
            _string_tuple(profile.payload.get("discharged_obstructions"))
        )
        critical = set(_string_tuple(profile.payload.get("critical_obstructions")))
        missing = tuple(sorted(critical - discharged_obstructions))
        if missing:
            problems.append(
                Problem(
                    code="obstruction.critical_undischarged",
                    message="obstruction profile has critical obstructions without discharge",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(profile.id, *missing),
                )
            )
    for obstruction in ledger.find(RecordType.OBSTRUCTION):
        obstruction_id = str(obstruction.payload.get("obstruction_id", obstruction.id))
        if (
            bool(obstruction.payload.get("critical", False))
            and obstruction_id not in discharged_obstructions
        ):
            problems.append(
                Problem(
                    code="obstruction.critical_undischarged",
                    message="critical obstruction remains undischarged",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(obstruction.id,),
                )
            )
    return tuple(problems)


def _validate_record_preserving_refinement(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    provenance_targets = {edge.target_id for edge in ledger.provenance_edges} | {
        edge.source_id for edge in ledger.provenance_edges
    }
    for refinement in ledger.find(RecordType.RECORD_PRESERVING_REFINEMENT):
        before = set(_string_tuple(refinement.payload.get("before_record_ids")))
        preserved = set(_string_tuple(refinement.payload.get("preserved_record_ids")))
        archived = set(_string_tuple(refinement.payload.get("archived_record_ids")))
        traced = before & provenance_targets
        missing = tuple(sorted(before - preserved - archived - traced))
        if missing:
            problems.append(
                Problem(
                    code="transition.record_not_preserved",
                    message="record-preserving refinement omits records without archive/provenance",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(refinement.id, *missing),
                )
            )
    return tuple(problems)


def _validate_self_modification(
    ledger: EvaluatedLedger, contract: ModeContract
) -> tuple[Problem, ...]:
    witnesses = ledger.find(RecordType.SELF_MODIFICATION_WITNESS)
    if (
        not witnesses
        and ledger.mode != "self_modification"
        and contract.name != "self_modification"
    ):
        return ()
    problems: list[Problem] = []
    if not witnesses:
        problems.append(
            Problem(
                code="self_modification.missing_lineage",
                message="self-modification mode needs a finite lineage witness",
                severity=ProblemSeverity.ERROR,
                related_record_ids=(ledger.agent_id,),
            )
        )
        return tuple(problems)
    required_check_disclosures = {
        "requirement_policy",
        "status_rule",
        "certificate_check",
        "failure_check",
        "compression_check",
    }
    for witness in witnesses:
        lineage_ok = bool(witness.payload.get("lineage_record_id")) or bool(
            str(witness.payload.get("lineage_reason", "")).strip()
        )
        if not lineage_ok:
            problems.append(
                Problem(
                    code="self_modification.missing_lineage",
                    message="self-modification witness lacks lineage record or reason",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(witness.id,),
                )
            )
        disclosed_checks = (
            set(_string_tuple(witness.payload.get("preserved_checks")))
            | set(_string_tuple(witness.payload.get("replaced_checks")))
            | set(_string_tuple(witness.payload.get("unavailable_checks")))
        )
        missing_checks = tuple(sorted(required_check_disclosures - disclosed_checks))
        if (
            not str(witness.payload.get("checker_version", "")).strip()
            or not str(witness.payload.get("rule_version", "")).strip()
            or missing_checks
        ):
            problems.append(
                Problem(
                    code="self_modification.missing_rule_disclosure",
                    message="self-modification witness lacks checker/rule version disclosure",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(witness.id, *missing_checks),
                )
            )
    return tuple(problems)


def _validate_compression_witnesses(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    factorization_by_class = {
        str(record.payload.get("profile_class_id", "")): record
        for record in ledger.find(RecordType.COMPRESSION_FACTORIZATION)
    }
    for profile_class in ledger.find(RecordType.COMPRESSION_PROFILE_CLASS):
        class_id = str(profile_class.payload.get("profile_class_id", profile_class.id))
        profiles = _string_tuple(profile_class.payload.get("profiles"))
        outputs_raw = profile_class.payload.get("admissibility_by_profile", {})
        compressed_raw = profile_class.payload.get("compressed_values", {})
        outputs = outputs_raw if isinstance(outputs_raw, dict) else {}
        compressed = compressed_raw if isinstance(compressed_raw, dict) else {}
        for index, left in enumerate(profiles):
            for right in profiles[index + 1 :]:
                if str(compressed.get(left, "")) == str(compressed.get(right, "")) and outputs.get(
                    left
                ) != outputs.get(right):
                    problems.append(
                        Problem(
                            code="compression.exactness_violation",
                            message=(
                                "compression merges profiles with different admissibility values"
                            ),
                            severity=ProblemSeverity.ERROR,
                            related_record_ids=(profile_class.id, left, right),
                        )
                    )
        factorization = factorization_by_class.get(class_id)
        if factorization is None:
            problems.append(
                Problem(
                    code="compression.factorization_missing",
                    message="compression profile class lacks a finite factorization witness",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(profile_class.id,),
                )
            )
            continue
        beta_raw = factorization.payload.get("beta_by_value", {})
        beta = beta_raw if isinstance(beta_raw, dict) else {}
        missing_values: list[str] = []
        mismatch_values: list[str] = []
        for profile in profiles:
            value = str(compressed.get(profile, ""))
            if value not in beta:
                missing_values.append(value)
                continue
            if beta.get(value) != outputs.get(profile):
                mismatch_values.append(value)
        if missing_values or not bool(factorization.payload.get("valid", True)):
            problems.append(
                Problem(
                    code="compression.factorization_missing",
                    message="compression factorization omits compressed values",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(factorization.id, *tuple(sorted(set(missing_values)))),
                )
            )
        if mismatch_values:
            problems.append(
                Problem(
                    code="compression.exactness_violation",
                    message="compression factorization disagrees with admissibility predicate",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(factorization.id, *tuple(sorted(set(mismatch_values)))),
                )
            )
    return tuple(problems)
