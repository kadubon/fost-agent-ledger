from __future__ import annotations

from .adequacy import validate_adequacy
from .certificates import CertificateRegistry, scope_covers
from .enums import (
    CERTIFICATE_USE_TO_SUPPORT_ROLE,
    Admissibility,
    AnchorKind,
    CertificateUseKind,
    EvidenceDisposition,
    EvidenceState,
    JudgmentKind,
    LedgerStage,
    ProblemSeverity,
    RecordType,
    Status,
    TargetState,
)
from .environment import EnvironmentToken, validate_environment_tokens
from .errors import UnknownModeError
from .formal import validate_formal_completion
from .ids import utc_now
from .kernels import Kernel, validate_kernel
from .ledger import EvaluatedLedger, stage_index
from .model import LedgerRecord, Problem, ValidationResult, parse_datetime
from .modes import ModeContract
from .obligations import Obligation, validate_obligations
from .provenance import validate_provenance
from .status import evaluate_status


def validate_ledger(
    ledger: EvaluatedLedger,
    mode: ModeContract | str | None = None,
    *,
    certificate_registry: CertificateRegistry | None = None,
    kernel: Kernel | None = None,
    require_finality: bool = False,
    strict_mode: bool = True,
    allow_unknown_mode_as_draft: bool = False,
) -> ValidationResult:
    try:
        contract = ModeContract.for_name(
            mode or ledger.mode,
            allow_unknown_as_draft=allow_unknown_mode_as_draft,
        )
    except UnknownModeError:
        if strict_mode:
            raise
        contract = ModeContract.for_name("draft")
    kernel = kernel or Kernel.from_ledger(ledger)
    payload_problems = ledger.validate_payloads()
    event_problems = ledger.event_order.validate()
    provenance_problems = validate_provenance(
        provenance_edges=ledger.provenance_edges,
        event_order=ledger.event_order,
        node_ids={record.id for record in ledger.records},
    )
    support_problems = ledger.support_graph.validate(ledger.event_order)
    stage_problems = _validate_stage_separation(ledger)
    stage_build_problems = ledger.validate_stage_builds()
    final_separation_problems = _validate_final_record_separation(ledger)
    certificate_problems = (
        certificate_registry.validate(support_graph=ledger.support_graph)
        if certificate_registry is not None
        else _certificate_problems_from_records(ledger)
    )
    environment_tokens = _environment_tokens_from_records(ledger)
    environment_problems = validate_environment_tokens(
        environment_tokens,
        required_names=contract.environment_token_selection_rules,
        high_impact=bool(contract.impact_requirements.get("required", False)),
    )
    kernel_problems = (
        validate_kernel(kernel)
        if kernel is not None
        else _validate_required_kernel_context(ledger, contract, require_finality=require_finality)
    )
    obligation_records = _obligations_from_records(ledger)
    obligation_problems = validate_obligations(obligation_records)
    adequacy = validate_adequacy(ledger, contract)
    formal_problems = validate_formal_completion(ledger, contract)
    strict_problems = (
        _validate_checked_finality(ledger, contract)
        + _validate_typed_anchors(ledger, require_declarations=require_finality)
        + _validate_persisted_adequacy(ledger, contract, require_finality=require_finality)
        + _validate_strict_stage_builds(ledger)
        if require_finality
        else ()
    )

    all_problems = (
        payload_problems
        + event_problems
        + provenance_problems
        + support_problems
        + stage_problems
        + stage_build_problems
        + final_separation_problems
        + certificate_problems
        + environment_problems
        + kernel_problems
        + obligation_problems
        + adequacy.problems
        + formal_problems
        + strict_problems
    )
    errors = tuple(
        problem
        for problem in all_problems
        if problem.severity in {ProblemSeverity.ERROR, ProblemSeverity.BLOCKER}
    )
    warnings = tuple(
        problem
        for problem in all_problems
        if problem.severity in {ProblemSeverity.INFO, ProblemSeverity.WARNING}
    )
    status = evaluate_status(ledger, all_problems)
    admissibility = _admissibility_for(status, contract, errors)
    issues = tuple(
        record
        for record in ledger.find(RecordType.ISSUE)
        if not bool(record.payload.get("resolved", False))
    )
    obligations = tuple(
        record
        for record in ledger.find(RecordType.OBLIGATION)
        if record.payload.get("lifecycle") not in {"discharged", "accepted_transfer"}
    )
    summary = _summary(status, admissibility, errors, warnings)
    return ValidationResult(
        status=status,
        admissibility=admissibility,
        errors=errors,
        warnings=warnings,
        issues=issues,
        obligations=obligations,
        missing_support=support_problems,
        certificate_problems=certificate_problems,
        environment_problems=environment_problems,
        summary=summary,
        records_checked=len(ledger.records),
    )


def assess_output(
    *,
    agent_id: str,
    mode: str,
    output: str,
    supports: list[str] | tuple[str, ...] = (),
    issues: list[str] | tuple[str, ...] = (),
    obligations: list[str] | tuple[str, ...] = (),
) -> ValidationResult:
    from .builder import LedgerBuilder

    builder = LedgerBuilder(agent_id=agent_id, mode=mode)
    claim = builder.add_claim(output)
    for support in supports:
        builder.add_support(support, supports=[claim.id])
    for issue in issues:
        builder.add_issue(issue)
    for obligation in obligations:
        builder.add_obligation(obligation, lifecycle="active", hard=False)
    return validate_ledger(builder.finalize(), mode=mode)


def _admissibility_for(
    status: Status,
    contract: ModeContract,
    errors: tuple[Problem, ...],
) -> Admissibility:
    if any(problem.severity == ProblemSeverity.BLOCKER for problem in errors):
        return Admissibility.BLOCKED
    if errors:
        return Admissibility.INADMISSIBLE
    if status in contract.admissible_status_region:
        return Admissibility.ADMISSIBLE
    if status == Status.REQUIRES_RECHECK:
        return Admissibility.REQUIRES_RECHECK
    if status == Status.UNKNOWN:
        return Admissibility.UNKNOWN
    return Admissibility.INADMISSIBLE


def _validate_stage_separation(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    seen_stage_for_id: dict[str, LedgerStage] = {}
    last_index = -1
    for record in ledger.records:
        index = stage_index(record.stage)
        if index < last_index:
            problems.append(
                Problem(
                    code="stage.out_of_order",
                    message="later ledger record appears before an earlier stage record",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id,),
                )
            )
        last_index = max(last_index, index)
        previous = seen_stage_for_id.get(record.id)
        if previous is not None and previous != record.stage:
            problems.append(
                Problem(
                    code="stage.rewrite",
                    message="same record id appears in multiple stages",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id,),
                )
            )
        seen_stage_for_id[record.id] = record.stage
    return tuple(problems)


def _validate_final_record_separation(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    records = {record.id: record for record in ledger.records}
    for record in ledger.records:
        if record.record_type == RecordType.STATUS:
            body_id = record.payload.get("body_record_id")
            if body_id == record.id or record.id in record.support_refs:
                problems.append(
                    Problem(
                        code="status.self_reference",
                        message="checked status cannot read or support itself",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(record.id,),
                    )
                )
        if record.record_type == RecordType.ADMISSIBILITY:
            body_id = record.payload.get("body_record_id")
            if body_id == record.id or record.id in record.support_refs:
                problems.append(
                    Problem(
                        code="admissibility.self_reference",
                        message="checked admissibility cannot read or support itself",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(record.id,),
                    )
                )
            body_record = records.get(str(body_id)) if body_id is not None else None
            if body_record is not None and body_record.record_type == RecordType.STATUS:
                problems.append(
                    Problem(
                        code="admissibility.checked_status_leakage",
                        message="admissibility body cannot use the final checked status record",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(record.id, body_record.id),
                    )
                )
            if record.payload.get("pre_admissibility_vector_id") == record.id:
                problems.append(
                    Problem(
                        code="admissibility.vector_self_reference",
                        message="pre-admissibility support vector excludes checked admissibility",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(record.id,),
                    )
                )
    for target in ledger.find(RecordType.CERTIFICATE_TARGET):
        if target.payload.get("judgment_kind") == "admissibility":
            problems.append(
                Problem(
                    code="certificate.admissibility_target_conflation",
                    message="admissibility does not introduce a separate certificate target",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(target.id,),
                )
            )
    return tuple(problems)


def _validate_checked_finality(
    ledger: EvaluatedLedger,
    contract: ModeContract,
) -> tuple[Problem, ...]:
    records = {record.id: record for record in ledger.records}
    problems: list[Problem] = []
    required = {
        RecordType.STATUS_BODY: "finality.missing_status_body",
        RecordType.CHECKED_STATUS: "finality.missing_checked_status",
        RecordType.PRE_ADMISSIBILITY_SUPPORT_VECTOR: "finality.missing_pre_vector",
        RecordType.ADMISSIBILITY_BODY: "finality.missing_admissibility_body",
        RecordType.CHECKED_ADMISSIBILITY: "finality.missing_checked_admissibility",
    }
    for record_type, code in required.items():
        if not ledger.find(record_type):
            problems.append(
                Problem(
                    code=code,
                    message=f"strict finality requires a {record_type.value} record",
                    severity=ProblemSeverity.ERROR,
                    suggested_repair=(
                        "Use LedgerBuilder.finalize_checked() or add the typed record."
                    ),
                )
            )

    checked_status_ids = {record.id for record in ledger.find(RecordType.CHECKED_STATUS)}
    checked_admissibility_ids = {
        record.id for record in ledger.find(RecordType.CHECKED_ADMISSIBILITY)
    }
    final_output_ids = (
        checked_status_ids
        | checked_admissibility_ids
        | {record.id for record in ledger.find(RecordType.STATUS)}
        | {record.id for record in ledger.find(RecordType.ADMISSIBILITY)}
    )

    for record in ledger.find(RecordType.STATUS_BODY) + ledger.find(RecordType.ADMISSIBILITY_BODY):
        _require_versions(record, problems, code_prefix="finality")
        if record.payload.get("reads_final_output", False):
            problems.append(_output_leakage_problem(record))
        for ref in record.support_refs:
            _check_support_ref(ledger, record, ref, problems)
        for ref_field in ("status_body_record_id", "pre_admissibility_vector_id"):
            ref_value = record.payload.get(ref_field)
            if isinstance(ref_value, str) and ref_value in final_output_ids:
                problems.append(_output_leakage_problem(record, ref_value))

    for record in ledger.find(RecordType.CHECKED_STATUS):
        _require_versions(record, problems, code_prefix="status")
        if not record.payload.get("checked", True):
            problems.append(
                Problem(
                    code="status.unchecked_final",
                    message="strict finality requires checked_status.checked=true",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id,),
                )
            )
        if record.payload.get("reads_final_output", False):
            problems.append(_output_leakage_problem(record))
        body_id = str(record.payload.get("body_record_id", ""))
        body = records.get(body_id)
        if body is None or body.record_type != RecordType.STATUS_BODY:
            problems.append(
                Problem(
                    code="status.missing_body",
                    message="checked status must point at a status_body record",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id, body_id),
                )
            )
        _require_coordinates(record, contract.required_read_coordinates, "read", problems)
        _require_coordinates(record, contract.required_respect_coordinates, "respect", problems)
        _check_no_self_support(record, problems, "status.self_reference")
        for ref in record.support_refs:
            _check_support_ref(ledger, record, ref, problems)

    for vector in ledger.find(RecordType.PRE_ADMISSIBILITY_SUPPORT_VECTOR):
        _require_versions(vector, problems, code_prefix="admissibility")
        if not any(
            vector.payload.get(key)
            for key in (
                "support_coordinates",
                "validator_coordinates",
                "kernel_coordinates",
                "certificate_coordinates",
                "environment_coordinates",
                "obligation_coordinates",
                "adequacy_coordinates",
            )
        ):
            problems.append(
                Problem(
                    code="admissibility.empty_pre_vector",
                    message="pre-admissibility support vector has no finite coordinates",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(vector.id,),
                )
            )
        if contract.required_respect_coordinates and not vector.payload.get(
            "validator_coordinates"
        ):
            problems.append(
                Problem(
                    code="admissibility.pre_vector_missing_coordinate",
                    message="pre-admissibility vector lacks validator coordinates",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(vector.id,),
                )
            )
        if contract.environment_token_selection_rules and not vector.payload.get(
            "environment_coordinates"
        ):
            problems.append(
                Problem(
                    code="admissibility.pre_vector_missing_coordinate",
                    message="pre-admissibility vector lacks environment coordinates",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(vector.id,),
                )
            )

    for record in ledger.find(RecordType.CHECKED_ADMISSIBILITY):
        _require_versions(record, problems, code_prefix="admissibility")
        if not record.payload.get("checked", True):
            problems.append(
                Problem(
                    code="admissibility.unchecked_final",
                    message="strict finality requires checked_admissibility.checked=true",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id,),
                )
            )
        if record.payload.get("reads_final_output", False):
            problems.append(_output_leakage_problem(record))
        body_id = str(record.payload.get("body_record_id", ""))
        body = records.get(body_id)
        if body is None or body.record_type != RecordType.ADMISSIBILITY_BODY:
            problems.append(
                Problem(
                    code="admissibility.missing_body",
                    message="checked admissibility must point at an admissibility_body record",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id, body_id),
                )
            )
        vector_id = str(record.payload.get("pre_admissibility_vector_id", ""))
        vector_record = records.get(vector_id)
        if (
            vector_record is None
            or vector_record.record_type != RecordType.PRE_ADMISSIBILITY_SUPPORT_VECTOR
        ):
            problems.append(
                Problem(
                    code="admissibility.missing_pre_vector",
                    message="checked admissibility must point at a pre-admissibility vector",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id, vector_id),
                )
            )
        _require_coordinates(record, contract.required_read_coordinates, "read", problems)
        _require_coordinates(record, contract.required_respect_coordinates, "respect", problems)
        _check_no_self_support(record, problems, "admissibility.self_reference")
        for ref in record.support_refs:
            if ref in final_output_ids and ref != record.id:
                problems.append(_output_leakage_problem(record, ref))
            _check_support_ref(ledger, record, ref, problems)
    return tuple(problems)


def _validate_typed_anchors(
    ledger: EvaluatedLedger,
    *,
    require_declarations: bool,
) -> tuple[Problem, ...]:
    if not require_declarations:
        return ()
    records = {record.id: record for record in ledger.records}
    declarations = {
        str(record.payload.get("anchor_id", "")): record
        for record in ledger.find(RecordType.ANCHOR_DECLARATION)
    }
    problems: list[Problem] = []
    for anchor_id in ledger.support_graph.anchors:
        declaration = declarations.get(anchor_id)
        if declaration is None:
            problems.append(
                Problem(
                    code="anchor.undeclared",
                    message="strict support anchor has no typed anchor declaration",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(anchor_id,),
                    suggested_repair="Add an anchor_declaration record for the support anchor.",
                )
            )
            continue
        target_id = str(declaration.payload.get("target_id", anchor_id))
        if target_id not in records and target_id != anchor_id:
            problems.append(
                Problem(
                    code="anchor.missing_target",
                    message="anchor declaration points at no finite target",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(declaration.id, target_id),
                )
            )
        kind = declaration.payload.get("anchor_kind")
        if kind == AnchorKind.OBSERVED_EVIDENCE.value and not (
            declaration.payload.get("provenance_ref") or declaration.payload.get("reason")
        ):
            problems.append(
                Problem(
                    code="anchor.missing_provenance",
                    message="observed-evidence anchor needs provenance or a finite reason",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(declaration.id, anchor_id),
                )
            )
        if kind == AnchorKind.EVENT_FREE_ROOT.value and not declaration.payload.get(
            "event_free", False
        ):
            problems.append(
                Problem(
                    code="anchor.event_free_mismatch",
                    message="event-free-root anchor must declare event_free=true",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(declaration.id, anchor_id),
                )
            )
        permitted = _payload_string_set(declaration, "permitted_roles")
        roles = ledger.support_graph.anchor_roles.get(anchor_id, ())
        if permitted and any(role.value not in permitted for role in roles):
            problems.append(
                Problem(
                    code="anchor.role_mismatch",
                    message="anchor declaration does not permit all graph anchor roles",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(declaration.id, anchor_id),
                )
            )
    return tuple(problems)


def _validate_persisted_adequacy(
    ledger: EvaluatedLedger,
    contract: ModeContract,
    *,
    require_finality: bool,
) -> tuple[Problem, ...]:
    if not require_finality:
        return ()
    records_by_component: dict[str, list[LedgerRecord]] = {}
    for record in ledger.find(RecordType.ADEQUACY_RECORD):
        records_by_component.setdefault(str(record.payload.get("component", "")), []).append(record)
    problems: list[Problem] = []
    for component in contract.adequacy_rules:
        candidates = records_by_component.get(component, [])
        if not candidates:
            problems.append(
                Problem(
                    code="adequacy.missing_record",
                    message=f"strict finality requires persisted adequacy record for {component}",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(component,),
                )
            )
            continue
        if not any(_adequacy_record_accepts(record) for record in candidates):
            problems.append(
                Problem(
                    code="adequacy.record_not_accepted",
                    message=f"persisted adequacy record for {component} is not accepted",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=tuple(record.id for record in candidates),
                )
            )
        for record in candidates:
            _require_versions(record, problems, code_prefix="adequacy")
            if record.payload.get("waived", False) and not (
                record.payload.get("support_refs") or record.payload.get("reason")
            ):
                problems.append(
                    Problem(
                        code="adequacy.waiver_missing_support",
                        message="adequacy waiver has no finite support or reason",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(record.id,),
                    )
                )
    return tuple(problems)


def _validate_required_kernel_context(
    ledger: EvaluatedLedger,
    contract: ModeContract,
    *,
    require_finality: bool,
) -> tuple[Problem, ...]:
    if not (
        require_finality
        or contract.name in {"agent_action", "self_modification"}
        or ledger.find(RecordType.SELF_MODIFICATION_WITNESS)
    ):
        return ()
    return (
        Problem(
            code="kernel.missing_context",
            message="mode requires finite validation/object kernel context",
            severity=ProblemSeverity.ERROR,
            suggested_repair=(
                "Add kernel_admission/root_debt records or pass a Kernel to validate_ledger()."
            ),
        ),
    )


def _validate_strict_stage_builds(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    finality_ids = {
        record.id
        for record in ledger.records
        if record.record_type
        in {
            RecordType.STATUS_BODY,
            RecordType.CHECKED_STATUS,
            RecordType.PRE_ADMISSIBILITY_SUPPORT_VECTOR,
            RecordType.ADMISSIBILITY_BODY,
            RecordType.CHECKED_ADMISSIBILITY,
        }
    }
    emitted = {record_id for build in ledger.stage_builds for record_id in build.emitted_records}
    problems: list[Problem] = []
    missing = sorted(finality_ids - emitted)
    for record_id in missing:
        problems.append(
            Problem(
                code="stage.missing_build_record",
                message="strict finality record is not emitted by a stage build",
                severity=ProblemSeverity.ERROR,
                related_record_ids=(record_id,),
            )
        )
    for build in ledger.stage_builds:
        if finality_ids & set(build.emitted_records) and (
            not build.rule_versions or not build.checker_versions
        ):
            problems.append(
                Problem(
                    code="stage.missing_checker_or_rule_version",
                    message="finality stage build needs checker and rule versions",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(build.build_id,),
                )
            )
    for record in ledger.records:
        if record.id in finality_ids and record.stage not in ledger.frozen_stages:
            problems.append(
                Problem(
                    code="stage.unfrozen_finality",
                    message="strict finality record stage is not frozen",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(record.id,),
                )
            )
    return tuple(problems)


def _require_versions(
    record: LedgerRecord,
    problems: list[Problem],
    *,
    code_prefix: str,
) -> None:
    if not record.payload.get("checker_version_id") or not record.payload.get("rule_version_id"):
        problems.append(
            Problem(
                code=f"{code_prefix}.missing_checker_or_rule_version",
                message="record lacks finite checker_version_id or rule_version_id",
                severity=ProblemSeverity.ERROR,
                related_record_ids=(record.id,),
            )
        )


def _require_coordinates(
    record: LedgerRecord,
    required: tuple[str, ...],
    kind: str,
    problems: list[Problem],
) -> None:
    present = _payload_string_set(record, f"{kind}_coordinates")
    missing = tuple(item for item in required if item not in present)
    if missing:
        problems.append(
            Problem(
                code=f"finality.missing_{kind}_coordinate",
                message=f"record lacks required {kind} coordinates: {', '.join(missing)}",
                severity=ProblemSeverity.ERROR,
                related_record_ids=(record.id, *missing),
            )
        )


def _check_no_self_support(record: LedgerRecord, problems: list[Problem], code: str) -> None:
    if (
        record.payload.get("body_record_id") == record.id
        or record.payload.get("pre_admissibility_vector_id") == record.id
        or record.id in record.support_refs
    ):
        problems.append(
            Problem(
                code=code,
                message="final checked record cannot read or support itself",
                severity=ProblemSeverity.ERROR,
                related_record_ids=(record.id,),
            )
        )


def _check_support_ref(
    ledger: EvaluatedLedger,
    record: LedgerRecord,
    ref: str,
    problems: list[Problem],
) -> None:
    if ref in ledger.support_graph.unavailable:
        problems.append(
            Problem(
                code="support.unavailable_evidence",
                message="unavailable leaf cannot serve as finality evidence",
                severity=ProblemSeverity.ERROR,
                related_record_ids=(record.id, ref),
            )
        )
        return
    if not any(item.id == ref for item in ledger.records):
        problems.append(
            Problem(
                code="support.missing_node",
                message="finality support_ref points at no finite record",
                severity=ProblemSeverity.ERROR,
                related_record_ids=(record.id, ref),
            )
        )


def _output_leakage_problem(record: LedgerRecord, ref: str | None = None) -> Problem:
    related = (record.id,) if ref is None else (record.id, ref)
    return Problem(
        code="finality.output_leakage",
        message="final checked output is read as an input to finality",
        severity=ProblemSeverity.ERROR,
        related_record_ids=related,
    )


def _adequacy_record_accepts(record: LedgerRecord) -> bool:
    state = record.payload.get("state")
    disposition = record.payload.get("disposition")
    if state == EvidenceState.PASS.value and disposition == EvidenceDisposition.ACCEPTED.value:
        return True
    return bool(record.payload.get("waived", False)) and disposition == (
        EvidenceDisposition.WAIVER_ACCEPTED.value
    )


def _payload_string_set(record: LedgerRecord, key: str) -> set[str]:
    raw = record.payload.get(key, ())
    if isinstance(raw, list):
        return {str(item) for item in raw}
    return set()


def _certificate_problems_from_records(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    certs = {
        str(record.payload.get("certificate_id", record.id)): record
        for record in ledger.find(RecordType.CERTIFICATE)
    }
    uses = ledger.find(RecordType.CERTIFICATE_USE)
    targets = {
        str(record.payload.get("target_id", record.id)): record
        for record in ledger.find(RecordType.CERTIFICATE_TARGET)
    }
    states = {
        (
            str(record.payload.get("certificate_id", "")),
            str(record.payload.get("target_id", "")),
        ): record
        for record in ledger.find(RecordType.CERTIFICATE_STATE)
    }
    problems: list[Problem] = []
    for use in uses:
        target_id = str(use.payload.get("target_id", ""))
        cert_id = str(use.payload.get("certificate_id", ""))
        target = targets.get(target_id)
        if target is None:
            problems.append(
                Problem(
                    code="certificate.missing_target",
                    message="certificate use cites no registered target",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(use.id, target_id),
                )
            )
            continue
        if target.payload.get("judgment_kind") == JudgmentKind.TRANSITION.value:
            continue
        target_state = TargetState(target.payload.get("target_state", TargetState.COMPLETE.value))
        if target_state != TargetState.COMPLETE:
            problems.append(
                Problem(
                    code="certificate.target_state_not_complete",
                    message="certificate target cannot pass with non-complete target state",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(target.id, str(target.payload.get("target_node", ""))),
                )
            )
        cert = certs.get(cert_id)
        if cert is None:
            problems.append(
                Problem(
                    code="certificate.unknown_certificate",
                    message="certificate use cites no finite certificate record",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(use.id, cert_id),
                )
            )
        else:
            expires_at = cert.payload.get("expires_at")
            if expires_at and parse_datetime(str(expires_at)) <= utc_now():
                problems.append(
                    Problem(
                        code="certificate.expired",
                        message="used certificate is expired for its target",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(use.id, cert.id, target.id),
                    )
                )
            metadata_raw = cert.payload.get("metadata", {})
            metadata = metadata_raw if isinstance(metadata_raw, dict) else {}
            for flag, code in {
                "revoked": "certificate.revoked",
                "issuer_conflict": "certificate.issuer_conflict",
                "monitor_expired": "certificate.monitor_expired",
                "kernel_mismatch": "certificate.kernel_mismatch",
            }.items():
                if metadata.get(flag, False):
                    problems.append(
                        Problem(
                            code=code,
                            message=f"used certificate has {flag.replace('_', ' ')}",
                            severity=ProblemSeverity.ERROR,
                            related_record_ids=(use.id, cert.id, target.id),
                        )
                    )
            cert_scope = cert.payload.get("scope", {})
            target_scope = target.payload.get("scope", {})
            if (
                isinstance(cert_scope, dict)
                and isinstance(target_scope, dict)
                and not scope_covers(cert_scope, target_scope)
            ):
                problems.append(
                    Problem(
                        code="certificate.scope_fail",
                        message="certificate scope does not cover target scope",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(use.id, cert.id, target.id),
                    )
                )
        if use.payload.get("judgment_kind") != target.payload.get(
            "judgment_kind"
        ) or use.payload.get("use_kind") != target.payload.get("use_kind"):
            problems.append(
                Problem(
                    code="certificate.target_mismatch",
                    message="certificate use judgment or use kind does not match target",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(use.id, target.id),
                )
            )
        if use.payload.get("target_node") != target.payload.get("target_node"):
            problems.append(
                Problem(
                    code="certificate.target_node_mismatch",
                    message="certificate use points at a different target node",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(use.id, target.id),
                )
            )
        state = states.get((cert_id, target_id))
        if state is None:
            problems.append(
                Problem(
                    code="certificate.missing_state",
                    message="certificate use has no separate certificate-state node",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(use.id, target.id),
                )
            )
        else:
            if state.id == str(target.payload.get("target_node", "")):
                problems.append(
                    Problem(
                        code="certificate.state_self_support",
                        message="certificate-state node must be separate from the target node",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(state.id, str(target.payload.get("target_node", ""))),
                    )
                )
            if state.payload.get("state") != "ok":
                problems.append(
                    Problem(
                        code="certificate.state_not_ok",
                        message="certificate state is not ok for used target",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(state.id, target.id),
                    )
                )
            role = CERTIFICATE_USE_TO_SUPPORT_ROLE[
                CertificateUseKind(str(target.payload.get("use_kind")))
            ]
            if not any(
                edge.source_id == state.id
                and edge.target_id == target.payload.get("target_node")
                and edge.role == role
                for edge in ledger.support_graph.edges
            ):
                problems.append(
                    Problem(
                        code="certificate.missing_support_edge",
                        message="certificate-state node lacks role-compatible support edge",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(state.id, str(target.payload.get("target_node", ""))),
                    )
                )
        state_in_use = use.payload.get("state", "unknown")
        if state_in_use not in {"ok", "unused"}:
            problems.append(
                Problem(
                    code="certificate.state_not_ok",
                    message=f"certificate use state is {state_in_use!r}",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(use.id,),
                )
            )
    for target in ledger.find(RecordType.CERTIFICATE_TARGET):
        if target.payload.get("judgment_kind") == JudgmentKind.TRANSITION.value:
            continue
        if (
            target.payload.get("target_state", TargetState.COMPLETE.value)
            != TargetState.COMPLETE.value
        ):
            problems.append(
                Problem(
                    code="certificate.target_state_not_complete",
                    message="certificate target state is not complete",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(target.id, str(target.payload.get("target_node", ""))),
                )
            )
        if target.payload.get("required", False) and target.payload.get("target_id") not in {
            use.payload.get("target_id") for use in uses
        }:
            problems.append(
                Problem(
                    code="certificate.empty_required_target",
                    message="required certificate target has no use",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(target.id,),
                )
            )
    return tuple(problems)


def _environment_tokens_from_records(ledger: EvaluatedLedger) -> tuple[EnvironmentToken, ...]:
    tokens: list[EnvironmentToken] = []
    for record in ledger.find(RecordType.ENVIRONMENT_TOKEN):
        payload = dict(record.payload)
        payload.setdefault("token_id", record.id)
        payload.setdefault("name", payload.get("kind", record.id))
        tokens.append(EnvironmentToken.from_dict(payload))
    return tuple(tokens)


def _obligations_from_records(ledger: EvaluatedLedger) -> tuple[Obligation, ...]:
    obligations: list[Obligation] = []
    for record in ledger.find(RecordType.OBLIGATION):
        payload = dict(record.payload)
        payload.setdefault("obligation_id", record.id)
        obligations.append(Obligation.from_dict(payload))
    return tuple(obligations)


def _summary(
    status: Status,
    admissibility: Admissibility,
    errors: tuple[Problem, ...],
    warnings: tuple[Problem, ...],
) -> str:
    if errors:
        return (
            f"status={status.value}; admissibility={admissibility.value}; "
            f"{len(errors)} blocking/error problem(s), {len(warnings)} warning/info problem(s)"
        )
    return f"status={status.value}; admissibility={admissibility.value}; finite checks completed"


def status_record(status: Status) -> LedgerRecord:
    return LedgerRecord.create(
        RecordType.STATUS,
        LedgerStage.CHECKED_STATUS,
        {"status": status.value},
        source="fost-agent-ledger",
    )
