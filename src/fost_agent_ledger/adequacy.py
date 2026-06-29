from __future__ import annotations

from dataclasses import dataclass

from .enums import (
    EvidenceDisposition,
    EvidenceState,
    ImpactLevel,
    ProblemSeverity,
    RecordType,
)
from .ledger import EvaluatedLedger
from .model import JsonModel, Problem
from .modes import ModeContract


@dataclass(frozen=True)
class EvidenceRecord(JsonModel):
    component: str
    state: EvidenceState
    disposition: EvidenceDisposition
    inputs: tuple[str, ...] = ()
    issues: tuple[str, ...] = ()
    obligations: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class ContractAdequacy(JsonModel):
    passed: bool
    records: tuple[EvidenceRecord, ...]
    problems: tuple[Problem, ...] = ()
    reason: str = ""


def validate_adequacy(ledger: EvaluatedLedger, mode: ModeContract) -> ContractAdequacy:
    records: list[EvidenceRecord] = []
    problems: list[Problem] = []
    checks = {
        "nonvacuity": anti_vacuity_check,
        "critic": critic_coverage_check,
        "environment": environment_selection_sufficiency_check,
        "scope": scope_exclusion_check,
        "impact": impact_default_check,
        "modeclosure": mode_closure_check,
        "compression": compression_use_check,
        "root_debt": root_debt_visibility_check,
        "obligation": obligation_adequacy_check,
    }
    for name in mode.adequacy_rules:
        check = checks.get(name)
        if check is None:
            continue
        record, record_problems = check(ledger, mode)
        records.append(record)
        problems.extend(record_problems)
    return ContractAdequacy(
        passed=not any(
            problem.severity in {ProblemSeverity.ERROR, ProblemSeverity.BLOCKER}
            for problem in problems
        ),
        records=tuple(records),
        problems=tuple(problems),
        reason="finite adequacy records checked",
    )


def anti_vacuity_check(
    ledger: EvaluatedLedger, mode: ModeContract
) -> tuple[EvidenceRecord, tuple[Problem, ...]]:
    has_claim = bool(ledger.find(RecordType.CLAIM))
    has_support = bool(ledger.find(RecordType.SUPPORT) or ledger.find(RecordType.EVIDENCE))
    has_issue_or_obligation = bool(
        ledger.find(RecordType.ISSUE) or ledger.find(RecordType.OBLIGATION)
    )
    consequential = _is_consequential(mode)
    if has_claim and (has_support or has_issue_or_obligation or not consequential):
        return _accepted("nonvacuity", "finite support or visible caveat is present"), ()
    problem = Problem(
        code="adequacy.vacuous",
        message="mode contract would be vacuous without support, issues, or obligations",
        severity=ProblemSeverity.ERROR if consequential else ProblemSeverity.WARNING,
        suggested_repair="Add support, an unresolved issue, or an obligation explaining the gap.",
    )
    return _blocked("nonvacuity", problem.message), (problem,)


def critic_coverage_check(
    ledger: EvaluatedLedger, mode: ModeContract
) -> tuple[EvidenceRecord, tuple[Problem, ...]]:
    if not mode.critic_role_requirements:
        return _accepted("critic", "mode does not require critic roles"), ()
    coverage = [
        record
        for record in ledger.find(RecordType.CRITIC_COVERAGE)
        if record.payload.get("role") in mode.critic_role_requirements
        and record.payload.get("covered", False)
    ]
    if coverage:
        return _accepted("critic", "required critic role is represented"), ()
    waivers = [
        record
        for record in ledger.find(RecordType.CRITIC_COVERAGE)
        if record.payload.get("waived", False)
    ]
    if waivers:
        return (
            EvidenceRecord(
                component="critic",
                state=EvidenceState.WAIVED,
                disposition=EvidenceDisposition.WAIVER_ACCEPTED,
                reason="critic coverage has a visible waiver",
            ),
            (),
        )
    problem = Problem(
        code="adequacy.critic_missing",
        message="required critic or external challenge role is not represented",
        severity=ProblemSeverity.WARNING
        if mode.name in {"draft", "research_summary"}
        else ProblemSeverity.ERROR,
        suggested_repair="Add a critic coverage record or an explicit waiver with support.",
    )
    return _blocked("critic", problem.message), (problem,)


def environment_selection_sufficiency_check(
    ledger: EvaluatedLedger, mode: ModeContract
) -> tuple[EvidenceRecord, tuple[Problem, ...]]:
    required = set(mode.environment_token_selection_rules)
    if not required:
        return _accepted("environment", "mode does not require selected environment tokens"), ()
    selected_kinds = {
        str(record.payload.get("kind"))
        for record in ledger.find(RecordType.ENVIRONMENT_TOKEN)
        if record.payload.get("selected", False)
    }
    missing = sorted(required - selected_kinds)
    if not missing:
        return _accepted("environment", "required environment token kinds are selected"), ()
    problem = Problem(
        code="adequacy.environment_selection",
        message=f"missing selected environment token kinds: {', '.join(missing)}",
        severity=ProblemSeverity.ERROR if _is_high_impact_mode(mode) else ProblemSeverity.WARNING,
    )
    return _blocked("environment", problem.message), (problem,)


def scope_exclusion_check(
    ledger: EvaluatedLedger, mode: ModeContract
) -> tuple[EvidenceRecord, tuple[Problem, ...]]:
    bad = [
        record
        for record in ledger.find(RecordType.SCOPE_EXCLUSION)
        if record.payload.get("disposition") in {"unresolved", "laundered", "conflict"}
    ]
    if not bad:
        return _accepted("scope", "no unresolved known scope exclusion"), ()
    problem = Problem(
        code="adequacy.scope_exclusion",
        message="known relevant scope exclusion remains unresolved",
        severity=ProblemSeverity.ERROR if _is_consequential(mode) else ProblemSeverity.WARNING,
        related_record_ids=tuple(record.id for record in bad),
    )
    return _blocked("scope", problem.message), (problem,)


def impact_default_check(
    ledger: EvaluatedLedger, mode: ModeContract
) -> tuple[EvidenceRecord, tuple[Problem, ...]]:
    if not mode.impact_requirements.get("required", False):
        return _accepted("impact", "impact classification is not required by the mode"), ()
    latest = ledger.latest(RecordType.IMPACT_RECORD)
    if latest is not None and latest.payload.get("impact") in {
        ImpactLevel.LOW.value,
        ImpactLevel.HIGH.value,
    }:
        return _accepted("impact", "impact classification is supported"), ()
    problem = Problem(
        code="adequacy.impact_unknown",
        message="impact is unknown by default for this mode",
        severity=ProblemSeverity.ERROR,
        suggested_repair=(
            "Add a supported impact record or keep the output inadmissible/recheckable."
        ),
    )
    return _blocked("impact", problem.message), (problem,)


def mode_closure_check(
    ledger: EvaluatedLedger, mode: ModeContract
) -> tuple[EvidenceRecord, tuple[Problem, ...]]:
    bad = [
        record
        for record in ledger.find(RecordType.MODE_CLOSURE)
        if record.payload.get("state", "pass") != "pass"
    ]
    if not bad:
        return _accepted("modeclosure", "no failed mode-closure record"), ()
    problem = Problem(
        code="adequacy.mode_closure",
        message="mode-closure record failed or requires transfer",
        severity=ProblemSeverity.ERROR,
        related_record_ids=tuple(record.id for record in bad),
    )
    return _blocked("modeclosure", problem.message), (problem,)


def compression_use_check(
    ledger: EvaluatedLedger, mode: ModeContract
) -> tuple[EvidenceRecord, tuple[Problem, ...]]:
    bad = [
        record
        for record in ledger.find(RecordType.COMPRESSION_USE)
        if record.payload.get("sufficient", True) is False
    ]
    if not bad:
        return _accepted("compression", "no insufficient compression use"), ()
    problem = Problem(
        code="adequacy.false_compression",
        message="lossy compression is not sufficient for the declared mode",
        severity=ProblemSeverity.ERROR,
        related_record_ids=tuple(record.id for record in bad),
    )
    return _blocked("compression", problem.message), (problem,)


def root_debt_visibility_check(
    ledger: EvaluatedLedger, mode: ModeContract
) -> tuple[EvidenceRecord, tuple[Problem, ...]]:
    hidden = [
        record
        for record in ledger.find(RecordType.ROOT_DEBT)
        if record.payload.get("visible", True) is False
    ]
    if not hidden:
        return _accepted("root_debt", "root debt is visible or absent"), ()
    problem = Problem(
        code="adequacy.root_debt_hidden",
        message="root debt record is hidden",
        severity=ProblemSeverity.ERROR,
        related_record_ids=tuple(record.id for record in hidden),
    )
    return _blocked("root_debt", problem.message), (problem,)


def obligation_adequacy_check(
    ledger: EvaluatedLedger, mode: ModeContract
) -> tuple[EvidenceRecord, tuple[Problem, ...]]:
    hard_open = [
        record
        for record in ledger.find(RecordType.OBLIGATION)
        if record.payload.get("hard", False)
        and record.payload.get("lifecycle") not in {"discharged", "accepted_transfer"}
    ]
    if not hard_open:
        return _accepted("obligation", "no hard open obligation"), ()
    problem = Problem(
        code="adequacy.hard_obligation",
        message="hard obligations remain open",
        severity=ProblemSeverity.BLOCKER,
        related_record_ids=tuple(record.id for record in hard_open),
    )
    return _blocked("obligation", problem.message), (problem,)


def _accepted(component: str, reason: str) -> EvidenceRecord:
    return EvidenceRecord(
        component=component,
        state=EvidenceState.PASS,
        disposition=EvidenceDisposition.ACCEPTED,
        reason=reason,
    )


def _blocked(component: str, reason: str) -> EvidenceRecord:
    return EvidenceRecord(
        component=component,
        state=EvidenceState.FAIL,
        disposition=EvidenceDisposition.BLOCKED,
        reason=reason,
    )


def _is_high_impact_mode(mode: ModeContract) -> bool:
    return bool(mode.impact_requirements.get("required", False))


def _is_consequential(mode: ModeContract) -> bool:
    return mode.name in {
        "code_generation",
        "safety_sensitive_advice",
        "publication",
        "agent_action",
        "self_modification",
    } or _is_high_impact_mode(mode)
