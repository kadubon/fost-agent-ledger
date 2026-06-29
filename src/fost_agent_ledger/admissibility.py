from __future__ import annotations

from .adequacy import validate_adequacy
from .certificates import CertificateRegistry, scope_covers
from .enums import (
    CERTIFICATE_USE_TO_SUPPORT_ROLE,
    Admissibility,
    CertificateUseKind,
    JudgmentKind,
    LedgerStage,
    ProblemSeverity,
    RecordType,
    Status,
    TargetState,
)
from .environment import EnvironmentToken, validate_environment_tokens
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
) -> ValidationResult:
    contract = ModeContract.for_name(mode or ledger.mode)
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
    kernel_problems = validate_kernel(kernel) if kernel is not None else ()
    obligation_records = _obligations_from_records(ledger)
    obligation_problems = validate_obligations(obligation_records)
    adequacy = validate_adequacy(ledger, contract)
    formal_problems = validate_formal_completion(ledger, contract)

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
