from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

from .enums import (
    Admissibility,
    CertificateStateValue,
    CertificateUseKind,
    EnvironmentTokenKind,
    EvidenceDisposition,
    EvidenceState,
    ImpactLevel,
    IssueSeverity,
    JudgmentKind,
    KernelAdmissionBasisKind,
    KernelAdmissionKind,
    KernelAdmissionStatus,
    ObligationLifecycle,
    RecordType,
    Status,
    TargetState,
    TokenState,
    UnavailablePolicy,
)
from .model import JsonDict, JsonModel, to_plain


class TypedPayload(JsonModel):
    record_type: ClassVar[RecordType]


@dataclass(frozen=True)
class TextPayload(TypedPayload):
    text: str
    reason: str = ""
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True)
class ClaimPayload(TextPayload):
    record_type: ClassVar[RecordType] = RecordType.CLAIM


@dataclass(frozen=True)
class SupportPayload(TextPayload):
    record_type: ClassVar[RecordType] = RecordType.SUPPORT


@dataclass(frozen=True)
class EvidencePayload(TextPayload):
    record_type: ClassVar[RecordType] = RecordType.EVIDENCE
    state: EvidenceState = EvidenceState.PASS
    disposition: EvidenceDisposition = EvidenceDisposition.ACCEPTED


@dataclass(frozen=True)
class ProcessClassPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.PROCESS_CLASS
    process_id: str
    class_name: str
    modes: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    challenge_roles: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class DistinctionBasisPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.DISTINCTION_BASIS
    basis_id: str
    distinctions: tuple[str, ...] = ()
    record_ids: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class FinitePresentationPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.FINITE_PRESENTATION
    presentation_id: str
    basis_id: str
    expression_id: str | None = None
    distinction_ids: tuple[str, ...] = ()
    record_ids: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class PresentationMapPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.PRESENTATION_MAP
    map_id: str
    presentation_id: str
    domain_distinctions: tuple[str, ...] = ()
    mapped_distinctions: tuple[str, ...] = ()
    target_records: tuple[str, ...] = ()
    total: bool = True
    reason: str = ""


@dataclass(frozen=True)
class FiniteExpressionPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.FINITE_EXPRESSION
    expression_id: str
    text: str
    presentation_id: str | None = None
    distinction_refs: tuple[str, ...] = ()
    record_refs: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class CertificatePayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.CERTIFICATE
    certificate_id: str
    issuer: str
    scope: JsonDict = field(default_factory=dict)
    issued_at: str | None = None
    expires_at: str | None = None
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True)
class CertificateTargetPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.CERTIFICATE_TARGET
    target_id: str
    judgment_kind: JudgmentKind
    use_kind: CertificateUseKind
    target_node: str
    event_id: str
    target_state: TargetState = TargetState.COMPLETE
    scope: JsonDict = field(default_factory=dict)
    required: bool = False


@dataclass(frozen=True)
class CertificateUsePayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.CERTIFICATE_USE
    use_id: str
    certificate_id: str
    target_id: str
    judgment_kind: JudgmentKind
    use_kind: CertificateUseKind
    target_node: str
    event_id: str = "event-0"
    state: CertificateStateValue = CertificateStateValue.UNKNOWN


@dataclass(frozen=True)
class CertificateStatePayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.CERTIFICATE_STATE
    state_id: str
    certificate_id: str
    target_id: str
    state: CertificateStateValue
    target_node: str
    reason: str = ""


@dataclass(frozen=True)
class RequirementPayload(TextPayload):
    record_type: ClassVar[RecordType] = RecordType.REQUIREMENT
    empty_requirement_reason: str | None = None


@dataclass(frozen=True)
class RequirementPolicyPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.REQUIREMENT_POLICY
    policy_id: str
    process_id: str = ""
    mode: str = ""
    requirements: tuple[str, ...] = ()
    issue_ids: tuple[str, ...] = ()
    empty: bool = False
    reason: str = ""


@dataclass(frozen=True)
class RequirementReasonPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.REQUIREMENT_REASON
    requirement_id: str
    source_policy_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class RequirementTransferPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.REQUIREMENT_TRANSFER
    requirement_id: str
    from_mode: str
    to_mode: str
    accepted: bool = True
    reason: str = ""


@dataclass(frozen=True)
class IssuePayload(TextPayload):
    record_type: ClassVar[RecordType] = RecordType.ISSUE
    issue_id: str = ""
    severity: IssueSeverity = IssueSeverity.MEDIUM
    blocking: bool = False
    resolved: bool = False


@dataclass(frozen=True)
class ResiduePayload(TextPayload):
    record_type: ClassVar[RecordType] = RecordType.RESIDUE
    distinction: str = ""
    mode_relevant: bool = True


@dataclass(frozen=True)
class ObstructionPayload(TextPayload):
    record_type: ClassVar[RecordType] = RecordType.OBSTRUCTION
    kind: str = "residual"
    mode: str = ""
    scope: JsonDict = field(default_factory=dict)
    blocks: tuple[str, ...] = ()
    critical: bool = False


@dataclass(frozen=True)
class SettlednessDeclarationPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.SETTLEDNESS_DECLARATION
    distinction_id: str
    presentation_id: str = ""
    declared_by: str = ""
    reason: str = ""


@dataclass(frozen=True)
class SettlednessLicensePayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.SETTLEDNESS_LICENSE
    license_id: str
    distinction_id: str
    presentation_id: str = ""
    licensed: bool = True
    checker_record_id: str = ""
    support_refs: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class ObstructionProfilePayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.OBSTRUCTION_PROFILE
    profile_id: str
    obstruction_ids: tuple[str, ...] = ()
    critical_obstructions: tuple[str, ...] = ()
    discharged_obstructions: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class UnavailableLeafPayload(TextPayload):
    record_type: ClassVar[RecordType] = RecordType.UNAVAILABLE_LEAF
    node_id: str = ""
    unavailable_policy: UnavailablePolicy = UnavailablePolicy.BLOCK
    evidence: bool = False


@dataclass(frozen=True)
class ObligationPayload(TextPayload):
    record_type: ClassVar[RecordType] = RecordType.OBLIGATION
    obligation_id: str = ""
    lifecycle: ObligationLifecycle = ObligationLifecycle.DECLARED
    hard: bool = False
    owner: str | None = None
    due_at: str | None = None
    support_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ObligationLifecyclePayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.OBLIGATION_LIFECYCLE
    obligation_id: str
    source: ObligationLifecycle
    target: ObligationLifecycle
    event_id: str = "event-0"
    deadline_status: str = "not_applicable"
    reason: str = ""


@dataclass(frozen=True)
class ObligationDischargePayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.OBLIGATION_DISCHARGE
    discharge_id: str
    obligation_id: str
    obstruction_id: str = ""
    certificate_cover_id: str = ""
    discharged: bool = True
    support_refs: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class EnvironmentTokenPayload(TextPayload):
    record_type: ClassVar[RecordType] = RecordType.ENVIRONMENT_TOKEN
    token_id: str = ""
    kind: EnvironmentTokenKind = EnvironmentTokenKind.ASSUMPTION
    name: str = ""
    state: TokenState = TokenState.UNKNOWN
    selected: bool = False
    known_relevant: bool = False
    freshness_at: str | None = None
    scope: JsonDict = field(default_factory=dict)


@dataclass(frozen=True)
class AcceptancePayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.ACCEPTANCE
    target_id: str
    accepted: bool = False
    accepted_by: tuple[str, ...] = ()
    blocked_by: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class AbstentionPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.ABSTENTION
    target_id: str
    abstained: bool = True
    obstructed: bool = False
    obstruction_refs: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class FailurePayload(TextPayload):
    record_type: ClassVar[RecordType] = RecordType.FAILURE
    failure_id: str = ""
    mode: str = ""
    relevant: bool = True
    blocking: bool = True
    resolved: bool = False
    severity: IssueSeverity = IssueSeverity.HIGH


@dataclass(frozen=True)
class ModeFilteredFailurePayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.MODE_FILTERED_FAILURE
    failure_id: str
    mode: str
    blocks: bool
    reason: str = ""


@dataclass(frozen=True)
class GateRequirementPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.GATE_REQUIREMENT
    impact_required: bool = False
    selected_tokens: tuple[str, ...] = ()
    required_certificates: tuple[str, ...] = ()
    required_obligations: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class GatePassPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.GATE_PASS
    passed: bool
    blocked_by: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class ImpactPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.IMPACT_RECORD
    impact: ImpactLevel
    reason: str = ""
    support_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class AdequacyPayload(TypedPayload):
    component: str
    state: EvidenceState
    disposition: EvidenceDisposition
    inputs: tuple[str, ...] = ()
    issues: tuple[str, ...] = ()
    obligations: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class CriticCoveragePayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.CRITIC_COVERAGE
    role: str = "external_challenge"
    covered: bool = False
    waived: bool = False
    reason: str = ""


@dataclass(frozen=True)
class ScopeExclusionPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.SCOPE_EXCLUSION
    item: str
    disposition: str
    reason: str = ""


@dataclass(frozen=True)
class ModeClosurePayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.MODE_CLOSURE
    state: str = "pass"
    reason: str = ""
    transferred_to_obligation: str | None = None


@dataclass(frozen=True)
class CompressionUsePayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.COMPRESSION_USE
    sufficient: bool
    reason: str = ""
    scope: JsonDict = field(default_factory=dict)


@dataclass(frozen=True)
class CompressionProfileClassPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.COMPRESSION_PROFILE_CLASS
    profile_class_id: str
    profiles: tuple[str, ...] = ()
    admissibility_by_profile: JsonDict = field(default_factory=dict)
    compressed_values: JsonDict = field(default_factory=dict)
    mode: str = ""
    reason: str = ""


@dataclass(frozen=True)
class CompressionFactorizationPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.COMPRESSION_FACTORIZATION
    factorization_id: str
    profile_class_id: str
    beta_by_value: JsonDict = field(default_factory=dict)
    valid: bool = True
    reason: str = ""


@dataclass(frozen=True)
class ConsistencyProfilePayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.CONSISTENCY_PROFILE
    profile_id: str
    passed: bool = True
    support_coordinates: tuple[str, ...] = ()
    kernel_coordinates: tuple[str, ...] = ()
    certificate_coordinates: tuple[str, ...] = ()
    environment_coordinates: tuple[str, ...] = ()
    obligation_coordinates: tuple[str, ...] = ()
    provenance_coordinates: tuple[str, ...] = ()
    compression_coordinates: tuple[str, ...] = ()
    status_coordinates: tuple[str, ...] = ()
    admissibility_coordinates: tuple[str, ...] = ()
    missing_coordinates: tuple[str, ...] = ()
    failed_coordinates: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class ValidatorTimeoutPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.VALIDATOR_TIMEOUT
    validator_id: str
    timeout_ms: int
    hidden: bool = False
    blocks: bool = True
    reason: str = ""


@dataclass(frozen=True)
class RootDebtPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.ROOT_DEBT
    root_declaration_id: str
    text: str
    visible: bool = True
    selected_as_obligation: bool = False


@dataclass(frozen=True)
class KernelAdmissionPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.KERNEL_ADMISSION
    admission_id: str
    version_id: str
    kind: KernelAdmissionKind
    status: KernelAdmissionStatus
    basis_kind: KernelAdmissionBasisKind
    checker_version_id: str
    event_id: str = "event-0"
    basis_id: str | None = None
    root_debt_id: str | None = None
    reason: str = ""
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True)
class NullCertificatePayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.NULL_CERTIFICATE
    certificate_id: str
    target_id: str
    allowed: bool = False
    reason: str = ""


@dataclass(frozen=True)
class CertificateCoverPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.CERTIFICATE_COVER
    cover_id: str
    obstruction_id: str
    certificate_id: str
    target_id: str
    discharged: bool = False
    support_refs: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class RespectCertificatePayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.RESPECT_CERTIFICATE
    respect_id: str
    subject_record_id: str
    required_coordinates: tuple[str, ...] = ()
    respected_coordinates: tuple[str, ...] = ()
    valid: bool = True
    reason: str = ""


@dataclass(frozen=True)
class RecordPreservingRefinementPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.RECORD_PRESERVING_REFINEMENT
    transition_id: str
    before_record_ids: tuple[str, ...] = ()
    preserved_record_ids: tuple[str, ...] = ()
    archived_record_ids: tuple[str, ...] = ()
    provenance_edge_ids: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class SelfModificationWitnessPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.SELF_MODIFICATION_WITNESS
    witness_id: str
    previous_process_id: str
    next_process_id: str
    lineage_record_id: str | None = None
    lineage_reason: str = ""
    checker_version: str = ""
    rule_version: str = ""
    kernel_update_record_id: str | None = None
    preserved_checks: tuple[str, ...] = ()
    replaced_checks: tuple[str, ...] = ()
    unavailable_checks: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class TheoryItemCoveragePayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.THEORY_ITEM_COVERAGE
    item_id: str
    coverage: str = "implemented"
    runtime_anchor: str = ""
    test_anchor: str = ""
    reason: str = ""
    anchor_refs: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StatusPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.STATUS
    status: Status
    body_record_id: str | None = None
    checked: bool = True
    read_coordinates: tuple[str, ...] = ()
    respect_coordinates: tuple[str, ...] = ()


@dataclass(frozen=True)
class AdmissibilityPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.ADMISSIBILITY
    admissibility: Admissibility
    body_record_id: str | None = None
    checked: bool = True
    pre_admissibility_vector_id: str | None = None
    read_coordinates: tuple[str, ...] = ()
    respect_coordinates: tuple[str, ...] = ()


@dataclass(frozen=True)
class TransitionWitnessPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.TRANSITION_WITNESS
    coordinate: str
    witness_record_id: str
    reason: str = ""


@dataclass(frozen=True)
class ValidationResultPayload(TypedPayload):
    record_type: ClassVar[RecordType] = RecordType.VALIDATION_RESULT
    status: Status
    admissibility: Admissibility
    summary: str = ""
    records_checked: int = 0
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


PAYLOAD_TYPES: dict[RecordType, type[TypedPayload]] = {
    RecordType.CLAIM: ClaimPayload,
    RecordType.SUPPORT: SupportPayload,
    RecordType.EVIDENCE: EvidencePayload,
    RecordType.PROCESS_CLASS: ProcessClassPayload,
    RecordType.DISTINCTION_BASIS: DistinctionBasisPayload,
    RecordType.FINITE_PRESENTATION: FinitePresentationPayload,
    RecordType.PRESENTATION_MAP: PresentationMapPayload,
    RecordType.FINITE_EXPRESSION: FiniteExpressionPayload,
    RecordType.CERTIFICATE: CertificatePayload,
    RecordType.CERTIFICATE_TARGET: CertificateTargetPayload,
    RecordType.CERTIFICATE_USE: CertificateUsePayload,
    RecordType.CERTIFICATE_STATE: CertificateStatePayload,
    RecordType.REQUIREMENT: RequirementPayload,
    RecordType.REQUIREMENT_POLICY: RequirementPolicyPayload,
    RecordType.REQUIREMENT_REASON: RequirementReasonPayload,
    RecordType.REQUIREMENT_TRANSFER: RequirementTransferPayload,
    RecordType.ISSUE: IssuePayload,
    RecordType.RESIDUE: ResiduePayload,
    RecordType.OBSTRUCTION: ObstructionPayload,
    RecordType.SETTLEDNESS_DECLARATION: SettlednessDeclarationPayload,
    RecordType.SETTLEDNESS_LICENSE: SettlednessLicensePayload,
    RecordType.OBSTRUCTION_PROFILE: ObstructionProfilePayload,
    RecordType.UNAVAILABLE_LEAF: UnavailableLeafPayload,
    RecordType.OBLIGATION: ObligationPayload,
    RecordType.OBLIGATION_LIFECYCLE: ObligationLifecyclePayload,
    RecordType.OBLIGATION_DISCHARGE: ObligationDischargePayload,
    RecordType.ENVIRONMENT_TOKEN: EnvironmentTokenPayload,
    RecordType.ACCEPTANCE: AcceptancePayload,
    RecordType.ABSTENTION: AbstentionPayload,
    RecordType.FAILURE: FailurePayload,
    RecordType.MODE_FILTERED_FAILURE: ModeFilteredFailurePayload,
    RecordType.GATE_REQUIREMENT: GateRequirementPayload,
    RecordType.GATE_PASS: GatePassPayload,
    RecordType.IMPACT_RECORD: ImpactPayload,
    RecordType.CRITIC_COVERAGE: CriticCoveragePayload,
    RecordType.SCOPE_EXCLUSION: ScopeExclusionPayload,
    RecordType.MODE_CLOSURE: ModeClosurePayload,
    RecordType.COMPRESSION_USE: CompressionUsePayload,
    RecordType.COMPRESSION_PROFILE_CLASS: CompressionProfileClassPayload,
    RecordType.COMPRESSION_FACTORIZATION: CompressionFactorizationPayload,
    RecordType.CONSISTENCY_PROFILE: ConsistencyProfilePayload,
    RecordType.VALIDATOR_TIMEOUT: ValidatorTimeoutPayload,
    RecordType.ROOT_DEBT: RootDebtPayload,
    RecordType.KERNEL_ADMISSION: KernelAdmissionPayload,
    RecordType.NULL_CERTIFICATE: NullCertificatePayload,
    RecordType.CERTIFICATE_COVER: CertificateCoverPayload,
    RecordType.RESPECT_CERTIFICATE: RespectCertificatePayload,
    RecordType.RECORD_PRESERVING_REFINEMENT: RecordPreservingRefinementPayload,
    RecordType.SELF_MODIFICATION_WITNESS: SelfModificationWitnessPayload,
    RecordType.THEORY_ITEM_COVERAGE: TheoryItemCoveragePayload,
    RecordType.STATUS: StatusPayload,
    RecordType.ADMISSIBILITY: AdmissibilityPayload,
    RecordType.TRANSITION_WITNESS: TransitionWitnessPayload,
    RecordType.VALIDATION_RESULT: ValidationResultPayload,
}


def payload_to_dict(payload: TypedPayload | dict[str, Any]) -> JsonDict:
    plain = to_plain(payload)
    if not isinstance(plain, dict):
        msg = "payload must serialize to a JSON object"
        raise TypeError(msg)
    return plain


def parse_payload(record_type: RecordType | str, payload: dict[str, Any]) -> TypedPayload:
    wanted = RecordType(record_type)
    payload_type = PAYLOAD_TYPES.get(wanted)
    if payload_type is None:
        return TextPayload(text=str(payload.get("text", "")), metadata=payload_to_dict(payload))
    normalized = _normalize_payload_values(payload_type, payload)
    return payload_type(**normalized)


def _normalize_payload_values(
    payload_type: type[TypedPayload], payload: dict[str, Any]
) -> dict[str, Any]:
    normalized = dict(payload)
    enum_fields: dict[str, type | None] = {
        "admissibility": Admissibility,
        "basis_kind": KernelAdmissionBasisKind,
        "disposition": EvidenceDisposition,
        "impact": ImpactLevel,
        "judgment_kind": JudgmentKind,
        "lifecycle": ObligationLifecycle,
        "severity": IssueSeverity,
        "state": _state_enum_for_payload(payload_type),
        "status": _status_enum_for_payload(payload_type),
        "source": _obligation_lifecycle_enum_for_payload(payload_type),
        "target": _obligation_lifecycle_enum_for_payload(payload_type),
        "kind": _kind_enum_for_payload(payload_type),
        "target_state": TargetState,
        "unavailable_policy": UnavailablePolicy,
        "use_kind": CertificateUseKind,
    }
    for key, enum_type in enum_fields.items():
        if key in normalized and enum_type is not None:
            normalized[key] = enum_type(normalized[key])
    for key in (
        "accepted_by",
        "archived_record_ids",
        "blocked_by",
        "blocks",
        "capabilities",
        "challenge_roles",
        "critical_obstructions",
        "discharged_obstructions",
        "distinction_ids",
        "distinction_refs",
        "distinctions",
        "domain_distinctions",
        "issue_ids",
        "mapped_distinctions",
        "modes",
        "obstruction_refs",
        "obstruction_ids",
        "preserved_checks",
        "preserved_record_ids",
        "profiles",
        "provenance_edge_ids",
        "record_ids",
        "record_refs",
        "replaced_checks",
        "requirements",
        "support_refs",
        "target_records",
        "unavailable_checks",
        "before_record_ids",
        "read_coordinates",
        "respect_coordinates",
        "required_coordinates",
        "respected_coordinates",
    ):
        if key in normalized and isinstance(normalized[key], list):
            normalized[key] = tuple(str(item) for item in normalized[key])
    for key in (
        "admissibility_coordinates",
        "certificate_coordinates",
        "compression_coordinates",
        "environment_coordinates",
        "failed_coordinates",
        "inputs",
        "issues",
        "kernel_coordinates",
        "missing_coordinates",
        "obligation_coordinates",
        "obligations",
        "provenance_coordinates",
        "selected_tokens",
        "status_coordinates",
        "support_coordinates",
        "required_certificates",
    ):
        if key in normalized and isinstance(normalized[key], list):
            normalized[key] = tuple(str(item) for item in normalized[key])
    if "required_obligations" in normalized and isinstance(
        normalized["required_obligations"], list
    ):
        normalized["required_obligations"] = tuple(
            str(item) for item in normalized["required_obligations"]
        )
    allowed = set(getattr(payload_type, "__dataclass_fields__", {}))
    normalized = {key: value for key, value in normalized.items() if key in allowed}
    return normalized


def _state_enum_for_payload(payload_type: type[TypedPayload]) -> type | None:
    if payload_type in {EvidencePayload, AdequacyPayload}:
        return EvidenceState
    if payload_type is CertificateStatePayload:
        return CertificateStateValue
    if payload_type is CertificateUsePayload:
        return CertificateStateValue
    if payload_type is EnvironmentTokenPayload:
        return TokenState
    return None


def _kind_enum_for_payload(payload_type: type[TypedPayload]) -> type | None:
    if payload_type is KernelAdmissionPayload:
        return KernelAdmissionKind
    if payload_type is EnvironmentTokenPayload:
        return EnvironmentTokenKind
    return None


def _status_enum_for_payload(payload_type: type[TypedPayload]) -> type | None:
    if payload_type is KernelAdmissionPayload:
        return KernelAdmissionStatus
    if payload_type in {StatusPayload, ValidationResultPayload}:
        return Status
    return None


def _obligation_lifecycle_enum_for_payload(payload_type: type[TypedPayload]) -> type | None:
    if payload_type is ObligationLifecyclePayload:
        return ObligationLifecycle
    return None
