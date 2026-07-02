from __future__ import annotations

from enum import Enum


class StableStrEnum(str, Enum):
    """String enum with stable lowercase JSON values."""

    def __str__(self) -> str:
        return str(self.value)


class LedgerStage(StableStrEnum):
    RAW = "raw"
    CANDIDATE = "candidate"
    SUPPORT = "support"
    CHECKED_CORE = "checked_core"
    CHECKED_POLICY = "checked_policy"
    CHECKED_STATUS = "checked_status"
    CHECKED_ADMISSIBILITY = "checked_admissibility"
    TRANSITION = "transition"
    FINAL = "final"


class PhaseLevel(StableStrEnum):
    RAW = "raw"
    CANDIDATE = "candidate"
    SUPPORT = "support"
    CORE_REQUIREMENT = "core_requirement"
    CORE_LICENSE = "core_license"
    CORE_RESIDUE = "core_residue"
    CORE_OBSTRUCTION = "core_obstruction"
    POLICY_SELECTION = "policy_selection"
    POLICY_GATE_REQUIREMENT = "policy_gate_requirement"
    POLICY_CERTIFICATE = "policy_certificate"
    POLICY_ENVIRONMENT = "policy_environment"
    POLICY_FAILURE = "policy_failure"
    POLICY_IMPACT = "policy_impact"
    POLICY_GENERATED_OBLIGATION = "policy_generated_obligation"
    POLICY_OBLIGATION = "policy_obligation"
    POLICY_GATE_PASS_ISSUE = "policy_gate_pass_issue"
    STATUS_BODY = "status_body"
    CHECKED_STATUS = "checked_status"
    ADMISSIBILITY_BODY = "admissibility_body"
    CHECKED_ADMISSIBILITY = "checked_admissibility"
    TRANSITION = "transition"


STAGE_ORDER: tuple[LedgerStage, ...] = (
    LedgerStage.RAW,
    LedgerStage.CANDIDATE,
    LedgerStage.SUPPORT,
    LedgerStage.CHECKED_CORE,
    LedgerStage.CHECKED_POLICY,
    LedgerStage.CHECKED_STATUS,
    LedgerStage.CHECKED_ADMISSIBILITY,
    LedgerStage.TRANSITION,
    LedgerStage.FINAL,
)

PHASE_ORDER: tuple[PhaseLevel, ...] = (
    PhaseLevel.RAW,
    PhaseLevel.CANDIDATE,
    PhaseLevel.SUPPORT,
    PhaseLevel.CORE_REQUIREMENT,
    PhaseLevel.CORE_LICENSE,
    PhaseLevel.CORE_RESIDUE,
    PhaseLevel.CORE_OBSTRUCTION,
    PhaseLevel.POLICY_SELECTION,
    PhaseLevel.POLICY_GATE_REQUIREMENT,
    PhaseLevel.POLICY_CERTIFICATE,
    PhaseLevel.POLICY_ENVIRONMENT,
    PhaseLevel.POLICY_FAILURE,
    PhaseLevel.POLICY_IMPACT,
    PhaseLevel.POLICY_GENERATED_OBLIGATION,
    PhaseLevel.POLICY_OBLIGATION,
    PhaseLevel.POLICY_GATE_PASS_ISSUE,
    PhaseLevel.STATUS_BODY,
    PhaseLevel.CHECKED_STATUS,
    PhaseLevel.ADMISSIBILITY_BODY,
    PhaseLevel.CHECKED_ADMISSIBILITY,
    PhaseLevel.TRANSITION,
)

DEFAULT_STAGE_PHASE: dict[LedgerStage, PhaseLevel] = {
    LedgerStage.RAW: PhaseLevel.RAW,
    LedgerStage.CANDIDATE: PhaseLevel.CANDIDATE,
    LedgerStage.SUPPORT: PhaseLevel.SUPPORT,
    LedgerStage.CHECKED_CORE: PhaseLevel.CORE_REQUIREMENT,
    LedgerStage.CHECKED_POLICY: PhaseLevel.POLICY_SELECTION,
    LedgerStage.CHECKED_STATUS: PhaseLevel.CHECKED_STATUS,
    LedgerStage.CHECKED_ADMISSIBILITY: PhaseLevel.CHECKED_ADMISSIBILITY,
    LedgerStage.TRANSITION: PhaseLevel.TRANSITION,
    LedgerStage.FINAL: PhaseLevel.CHECKED_ADMISSIBILITY,
}


class RecordType(StableStrEnum):
    CLAIM = "claim"
    SUPPORT = "support"
    EVIDENCE = "evidence"
    PROCESS_CLASS = "process_class"
    DISTINCTION_BASIS = "distinction_basis"
    FINITE_PRESENTATION = "finite_presentation"
    PRESENTATION_MAP = "presentation_map"
    FINITE_EXPRESSION = "finite_expression"
    CERTIFICATE = "certificate"
    CERTIFICATE_TARGET = "certificate_target"
    CERTIFICATE_USE = "certificate_use"
    CERTIFICATE_STATE = "certificate_state"
    REQUIREMENT = "requirement"
    REQUIREMENT_POLICY = "requirement_policy"
    REQUIREMENT_REASON = "requirement_reason"
    REQUIREMENT_TRANSFER = "requirement_transfer"
    ISSUE = "issue"
    RESIDUE = "residue"
    OBSTRUCTION = "obstruction"
    SETTLEDNESS_DECLARATION = "settledness_declaration"
    SETTLEDNESS_LICENSE = "settledness_license"
    OBSTRUCTION_PROFILE = "obstruction_profile"
    UNAVAILABLE_LEAF = "unavailable_leaf"
    OBLIGATION = "obligation"
    OBLIGATION_LIFECYCLE = "obligation_lifecycle"
    OBLIGATION_DISCHARGE = "obligation_discharge"
    ENVIRONMENT_TOKEN = "environment_token"
    ACCEPTANCE = "acceptance"
    ABSTENTION = "abstention"
    FAILURE = "failure"
    MODE_FILTERED_FAILURE = "mode_filtered_failure"
    GATE_REQUIREMENT = "gate_requirement"
    GATE_PASS = "gate_pass"
    IMPACT_RECORD = "impact_record"
    CRITIC_COVERAGE = "critic_coverage"
    SCOPE_EXCLUSION = "scope_exclusion"
    MODE_CLOSURE = "mode_closure"
    COMPRESSION_USE = "compression_use"
    COMPRESSION_PROFILE_CLASS = "compression_profile_class"
    COMPRESSION_FACTORIZATION = "compression_factorization"
    CONSISTENCY_PROFILE = "consistency_profile"
    VALIDATOR_TIMEOUT = "validator_timeout"
    ROOT_DEBT = "root_debt"
    KERNEL_ADMISSION = "kernel_admission"
    ANCHOR_DECLARATION = "anchor_declaration"
    ADEQUACY_RECORD = "adequacy_record"
    STATUS_BODY = "status_body"
    CHECKED_STATUS = "checked_status"
    PRE_ADMISSIBILITY_SUPPORT_VECTOR = "pre_admissibility_support_vector"
    ADMISSIBILITY_BODY = "admissibility_body"
    CHECKED_ADMISSIBILITY = "checked_admissibility"
    NULL_CERTIFICATE = "null_certificate"
    CERTIFICATE_COVER = "certificate_cover"
    RESPECT_CERTIFICATE = "respect_certificate"
    RECORD_PRESERVING_REFINEMENT = "record_preserving_refinement"
    SELF_MODIFICATION_WITNESS = "self_modification_witness"
    THEORY_ITEM_COVERAGE = "theory_item_coverage"
    STATUS = "status"
    ADMISSIBILITY = "admissibility"
    TRANSITION_WITNESS = "transition_witness"
    VALIDATION_RESULT = "validation_result"


class SupportRole(StableStrEnum):
    DATA = "data"
    ENVIRONMENT = "environment"
    KERNEL_ADMISSION = "kernel_admission"
    RULE_INVOCATION = "rule_invocation"
    CHECKER_INVOCATION = "checker_invocation"
    REQUIREMENT = "requirement"
    ISSUE = "issue"
    LICENSE = "license"
    RESIDUE = "residue"
    OBSTRUCTION = "obstruction"
    CERTIFICATE_STATE = "certificate_state"
    COVER = "cover"
    GATE_REQUIREMENT = "gate_requirement"
    GATE_PASS = "gate_pass"
    ENVIRONMENT_STATE = "environment_state"
    FAILURE_FILTER = "failure_filter"
    IMPACT = "impact"
    OBLIGATION_LIFECYCLE = "obligation_lifecycle"
    ACCEPTANCE = "acceptance"
    ABSTENTION = "abstention"
    CONSISTENCY_PROFILE = "consistency_profile"
    RESPECT_CERTIFICATE = "respect_certificate"
    STATUS_BODY = "status_body"
    STATUS_CHECK = "status_check"
    ADMISSIBILITY_BODY = "admissibility_body"
    ADMISSIBILITY_CHECK = "admissibility_check"
    TRANSITION = "transition"


class CertificateUseKind(StableStrEnum):
    COVER = "cover"
    GATE = "gate"
    KERNEL = "kernel"
    LICENSE = "license"
    STATUS = "status"
    TRANSITION = "transition"
    RESPECT = "respect"


CERTIFICATE_USE_TO_SUPPORT_ROLE: dict[CertificateUseKind, SupportRole] = {
    CertificateUseKind.COVER: SupportRole.COVER,
    CertificateUseKind.GATE: SupportRole.GATE_PASS,
    CertificateUseKind.KERNEL: SupportRole.KERNEL_ADMISSION,
    CertificateUseKind.LICENSE: SupportRole.LICENSE,
    CertificateUseKind.STATUS: SupportRole.STATUS_CHECK,
    CertificateUseKind.TRANSITION: SupportRole.TRANSITION,
    CertificateUseKind.RESPECT: SupportRole.CHECKER_INVOCATION,
}


class JudgmentKind(StableStrEnum):
    CORE = "core"
    POLICY = "policy"
    STATUS = "status"
    ADMISSIBILITY = "admissibility"
    TRANSITION = "transition"
    KERNEL = "kernel"


class Necessity(StableStrEnum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    DIAGNOSTIC = "diagnostic"


class UnavailablePolicy(StableStrEnum):
    BLOCK = "block"
    CARRY = "carry"
    TRANSFER = "transfer"
    RECHECK = "recheck"
    IGNORE = "ignore"


class AnchorKind(StableStrEnum):
    ROOT_DECLARATION = "root_declaration"
    PRIOR_KERNEL_WITNESS = "prior_kernel_witness"
    EVENT_FREE_ROOT = "event_free_root"
    EXTERNAL_CERTIFICATE_ANCHOR = "external_certificate_anchor"
    OBSERVED_EVIDENCE = "observed_evidence"
    DECLARED_SUPPORT = "declared_support"


class CoordinateKind(StableStrEnum):
    SUPPORT = "support"
    KERNEL = "kernel"
    CERTIFICATE = "certificate"
    OBLIGATION = "obligation"
    ENVIRONMENT = "environment"
    MODE_SCOPE = "mode_scope"
    PROVENANCE = "provenance"
    EVENT_ORDER = "event_order"
    STATUS = "status"
    ADMISSIBILITY = "admissibility"
    VALIDATOR = "validator"
    ADEQUACY = "adequacy"


class EvidenceState(StableStrEnum):
    PASS = "pass"
    FAIL = "fail"
    WAIVED = "waived"
    TRANSFERRED = "transferred"
    RECHECK_OPEN = "recheck_open"
    CONFLICT = "conflict"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class EvidenceDisposition(StableStrEnum):
    ACCEPTED = "accepted"
    BLOCKED = "blocked"
    WAIVER_ACCEPTED = "waiver_accepted"
    TRANSFER_ACCEPTED = "transfer_accepted"
    RECHECK_ACCEPTED = "recheck_accepted"
    ISSUE_OPEN = "issue_open"
    OBLIGATION_OPEN = "obligation_open"
    CONFLICT = "conflict"


class TargetState(StableStrEnum):
    COMPLETE = "complete"
    MISSING_TARGET = "missing_target"
    MISSING_REQUIRED = "missing_required"
    MISSING_USE = "missing_use"
    WAIVER_PENDING = "waiver_pending"
    TRANSFERRED = "transferred"
    RECHECK_OPEN = "recheck_open"
    STATE_FAIL = "state_fail"
    CONFLICT = "conflict"


class CertificateStateValue(StableStrEnum):
    OK = "ok"
    STALE = "stale"
    SCOPE_FAIL = "scope_fail"
    KERNEL_MISMATCH = "kernel_mismatch"
    MONITOR_EXPIRED = "monitor_expired"
    UNKNOWN = "unknown"
    CONFLICT = "conflict"
    UNUSED = "unused"


class ObligationLifecycle(StableStrEnum):
    UNDECLARED = "undeclared"
    DECLARED = "declared"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    CARRIED = "carried"
    TRANSFERRED = "transferred"
    ACCEPTED_TRANSFER = "accepted_transfer"
    BLOCKED = "blocked"
    DISCHARGED = "discharged"
    CONFLICT = "conflict"
    EXPIRED = "expired"
    FAILED = "failed"


class DeadlineStatus(StableStrEnum):
    NOT_DUE = "not_due"
    MET = "met"
    MISSED = "missed"
    EXPIRED = "expired"
    NOT_APPLICABLE = "not_applicable"


class EnvironmentTokenKind(StableStrEnum):
    ASSUMPTION = "assumption"
    FRESHNESS = "freshness"
    BOUNDARY = "boundary"
    MONITOR = "monitor"
    EXTERNAL_CONDITION = "external_condition"
    DATA_AGE = "data_age"
    TOOL_STATE = "tool_state"
    MODEL_VERSION = "model_version"
    POLICY_VERSION = "policy_version"


class TokenState(StableStrEnum):
    OK = "ok"
    STALE = "stale"
    FAILED = "failed"
    DRIFT = "drift"
    UNKNOWN = "unknown"
    CONFLICT = "conflict"
    UNSELECTED = "unselected"


class Status(StableStrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"
    REQUIRES_RECHECK = "requires_recheck"
    INVALID = "invalid"


class Admissibility(StableStrEnum):
    ADMISSIBLE = "admissible"
    INADMISSIBLE = "inadmissible"
    CARRIED = "carried"
    TRANSFERRED = "transferred"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"
    REQUIRES_RECHECK = "requires_recheck"


class IssueSeverity(StableStrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProblemSeverity(StableStrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class ImpactLevel(StableStrEnum):
    LOW = "low"
    HIGH = "high"
    UNKNOWN = "unknown"
    CONFLICT = "conflict"


class KernelAdmissionKind(StableStrEnum):
    RULE = "rule"
    CHECKER = "checker"


class KernelAdmissionStatus(StableStrEnum):
    ADMITTED = "admitted"
    REJECTED = "rejected"
    UNAVAILABLE = "unavailable"
    SUPERSEDED = "superseded"


class KernelAdmissionBasisKind(StableStrEnum):
    ROOT = "root"
    PRIOR_KERNEL = "prior_kernel"
    EXTERNAL_CERTIFICATE = "external_certificate"
    SELF = "self"


class ModeName(StableStrEnum):
    DRAFT = "draft"
    RESEARCH_SUMMARY = "research_summary"
    CODE_GENERATION = "code_generation"
    SAFETY_SENSITIVE_ADVICE = "safety_sensitive_advice"
    PUBLICATION = "publication"
    AGENT_ACTION = "agent_action"
    SELF_MODIFICATION = "self_modification"
