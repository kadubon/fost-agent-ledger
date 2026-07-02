from __future__ import annotations

from enum import Enum
from typing import Any

from ..enums import (
    Admissibility,
    AnchorKind,
    CertificateStateValue,
    CertificateUseKind,
    CoordinateKind,
    DeadlineStatus,
    EnvironmentTokenKind,
    EvidenceDisposition,
    EvidenceState,
    ImpactLevel,
    IssueSeverity,
    JudgmentKind,
    KernelAdmissionBasisKind,
    KernelAdmissionKind,
    KernelAdmissionStatus,
    LedgerStage,
    ObligationLifecycle,
    PhaseLevel,
    RecordType,
    Status,
    SupportRole,
    TargetState,
    TokenState,
    UnavailablePolicy,
)


def export_json_schema() -> dict[str, Any]:
    """Return the portable v2.0 JSON Schema bundle for public objects."""

    defs = _defs()
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.org/fost-agent-ledger-2.0.schema.json",
        "title": "fost-agent-ledger v2.0",
        "oneOf": [
            {"$ref": "#/$defs/EvaluatedLedger"},
            {"$ref": "#/$defs/OperationalCut"},
            {"$ref": "#/$defs/LedgerTransition"},
            {"$ref": "#/$defs/CertificateRegistry"},
            {"$ref": "#/$defs/Kernel"},
            {
                "type": "object",
                "required": ["ledger"],
                "properties": {"ledger": {"$ref": "#/$defs/EvaluatedLedger"}},
                "additionalProperties": False,
            },
        ],
        "$defs": defs,
    }


def _defs() -> dict[str, Any]:
    return {
        "JsonObject": {"type": "object"},
        "StringArray": {"type": "array", "items": {"type": "string"}},
        "Problem": _problem_schema(),
        "ValidationCoordinate": _validation_coordinate_schema(),
        "EventOrder": _event_order_schema(),
        "ProvenanceEdge": _provenance_edge_schema(),
        "StageBuildRecord": _stage_build_schema(),
        "SupportEdge": _support_edge_schema(),
        "FrontierItem": _frontier_item_schema(),
        "SupportGraph": _support_graph_schema(),
        "LedgerRecord": _ledger_record_schema(),
        "EvaluatedLedger": _ledger_schema(),
        "OperationalCut": _cut_schema(),
        "TransitionWitness": _transition_witness_schema(),
        "LedgerTransition": _transition_schema(),
        "Certificate": _certificate_schema(),
        "CertificateTarget": _certificate_target_schema(),
        "RequiredCertificate": _required_certificate_schema(),
        "CertificateUse": _certificate_use_schema(),
        "CertificateState": _certificate_state_schema(),
        "CertificateRegistry": _certificate_registry_schema(),
        "KernelAdmission": _kernel_admission_schema(),
        "Kernel": _kernel_schema(),
        "ValidationResult": _validation_result_schema(),
        **_payload_schemas(),
    }


def _ledger_record_schema() -> dict[str, Any]:
    payload_conditions = []
    for record_type, payload_def in {
        RecordType.CLAIM: "TextPayload",
        RecordType.SUPPORT: "TextPayload",
        RecordType.EVIDENCE: "EvidencePayload",
        RecordType.PROCESS_CLASS: "ProcessClassPayload",
        RecordType.DISTINCTION_BASIS: "DistinctionBasisPayload",
        RecordType.FINITE_PRESENTATION: "FinitePresentationPayload",
        RecordType.PRESENTATION_MAP: "PresentationMapPayload",
        RecordType.FINITE_EXPRESSION: "FiniteExpressionPayload",
        RecordType.CERTIFICATE: "CertificatePayload",
        RecordType.CERTIFICATE_TARGET: "CertificateTargetPayload",
        RecordType.CERTIFICATE_USE: "CertificateUsePayload",
        RecordType.CERTIFICATE_STATE: "CertificateStatePayload",
        RecordType.REQUIREMENT: "RequirementPayload",
        RecordType.REQUIREMENT_POLICY: "RequirementPolicyPayload",
        RecordType.REQUIREMENT_REASON: "RequirementReasonPayload",
        RecordType.REQUIREMENT_TRANSFER: "RequirementTransferPayload",
        RecordType.ISSUE: "IssuePayload",
        RecordType.RESIDUE: "ResiduePayload",
        RecordType.OBSTRUCTION: "ObstructionPayload",
        RecordType.SETTLEDNESS_DECLARATION: "SettlednessDeclarationPayload",
        RecordType.SETTLEDNESS_LICENSE: "SettlednessLicensePayload",
        RecordType.OBSTRUCTION_PROFILE: "ObstructionProfilePayload",
        RecordType.UNAVAILABLE_LEAF: "UnavailableLeafPayload",
        RecordType.OBLIGATION: "ObligationPayload",
        RecordType.OBLIGATION_LIFECYCLE: "ObligationLifecyclePayload",
        RecordType.OBLIGATION_DISCHARGE: "ObligationDischargePayload",
        RecordType.ENVIRONMENT_TOKEN: "EnvironmentTokenPayload",
        RecordType.ACCEPTANCE: "AcceptancePayload",
        RecordType.ABSTENTION: "AbstentionPayload",
        RecordType.FAILURE: "FailurePayload",
        RecordType.MODE_FILTERED_FAILURE: "ModeFilteredFailurePayload",
        RecordType.GATE_REQUIREMENT: "GateRequirementPayload",
        RecordType.GATE_PASS: "GatePassPayload",
        RecordType.IMPACT_RECORD: "ImpactPayload",
        RecordType.CRITIC_COVERAGE: "CriticCoveragePayload",
        RecordType.SCOPE_EXCLUSION: "ScopeExclusionPayload",
        RecordType.MODE_CLOSURE: "ModeClosurePayload",
        RecordType.COMPRESSION_USE: "CompressionUsePayload",
        RecordType.COMPRESSION_PROFILE_CLASS: "CompressionProfileClassPayload",
        RecordType.COMPRESSION_FACTORIZATION: "CompressionFactorizationPayload",
        RecordType.CONSISTENCY_PROFILE: "ConsistencyProfilePayload",
        RecordType.VALIDATOR_TIMEOUT: "ValidatorTimeoutPayload",
        RecordType.ROOT_DEBT: "RootDebtPayload",
        RecordType.KERNEL_ADMISSION: "KernelAdmissionPayload",
        RecordType.ANCHOR_DECLARATION: "AnchorDeclarationPayload",
        RecordType.ADEQUACY_RECORD: "AdequacyRecordPayload",
        RecordType.STATUS_BODY: "StatusBodyPayload",
        RecordType.CHECKED_STATUS: "CheckedStatusPayload",
        RecordType.PRE_ADMISSIBILITY_SUPPORT_VECTOR: "PreAdmissibilitySupportVectorPayload",
        RecordType.ADMISSIBILITY_BODY: "AdmissibilityBodyPayload",
        RecordType.CHECKED_ADMISSIBILITY: "CheckedAdmissibilityPayload",
        RecordType.NULL_CERTIFICATE: "NullCertificatePayload",
        RecordType.CERTIFICATE_COVER: "CertificateCoverPayload",
        RecordType.RESPECT_CERTIFICATE: "RespectCertificatePayload",
        RecordType.RECORD_PRESERVING_REFINEMENT: "RecordPreservingRefinementPayload",
        RecordType.SELF_MODIFICATION_WITNESS: "SelfModificationWitnessPayload",
        RecordType.THEORY_ITEM_COVERAGE: "TheoryItemCoveragePayload",
        RecordType.STATUS: "StatusPayload",
        RecordType.ADMISSIBILITY: "AdmissibilityPayload",
        RecordType.TRANSITION_WITNESS: "TransitionWitnessPayload",
        RecordType.VALIDATION_RESULT: "ValidationResultPayload",
    }.items():
        payload_conditions.append(
            {
                "if": {"properties": {"record_type": {"const": record_type.value}}},
                "then": {"properties": {"payload": {"$ref": f"#/$defs/{payload_def}"}}},
            }
        )
    return {
        "type": "object",
        "required": ["id", "record_type", "stage", "event_id", "timestamp", "payload"],
        "properties": {
            "id": {"type": "string"},
            "record_type": {"type": "string", "enum": _enum(RecordType)},
            "stage": {"type": "string", "enum": _enum(LedgerStage)},
            "event_id": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "source": {"type": "string"},
            "payload": {"type": "object"},
            "support_refs": {"$ref": "#/$defs/StringArray"},
            "metadata": {"$ref": "#/$defs/JsonObject"},
        },
        "allOf": payload_conditions,
        "additionalProperties": False,
    }


def _payload_schemas() -> dict[str, Any]:
    return {
        "TextPayload": _object({"text": {"type": "string"}}, ["text"]),
        "EvidencePayload": _object(
            {
                "text": {"type": "string"},
                "state": {"type": "string", "enum": _enum(EvidenceState)},
                "disposition": {"type": "string", "enum": _enum(EvidenceDisposition)},
                "reason": {"type": "string"},
                "metadata": {"$ref": "#/$defs/JsonObject"},
            },
            ["text"],
        ),
        "ProcessClassPayload": _object(
            {
                "process_id": {"type": "string"},
                "class_name": {"type": "string"},
                "modes": {"$ref": "#/$defs/StringArray"},
                "capabilities": {"$ref": "#/$defs/StringArray"},
                "challenge_roles": {"$ref": "#/$defs/StringArray"},
                "reason": {"type": "string"},
            },
            ["process_id", "class_name"],
        ),
        "DistinctionBasisPayload": _object(
            {
                "basis_id": {"type": "string"},
                "distinctions": {"$ref": "#/$defs/StringArray"},
                "record_ids": {"$ref": "#/$defs/StringArray"},
                "reason": {"type": "string"},
            },
            ["basis_id"],
        ),
        "FinitePresentationPayload": _object(
            {
                "presentation_id": {"type": "string"},
                "basis_id": {"type": "string"},
                "expression_id": {"type": ["string", "null"]},
                "distinction_ids": {"$ref": "#/$defs/StringArray"},
                "record_ids": {"$ref": "#/$defs/StringArray"},
                "reason": {"type": "string"},
            },
            ["presentation_id", "basis_id"],
        ),
        "PresentationMapPayload": _object(
            {
                "map_id": {"type": "string"},
                "presentation_id": {"type": "string"},
                "domain_distinctions": {"$ref": "#/$defs/StringArray"},
                "mapped_distinctions": {"$ref": "#/$defs/StringArray"},
                "target_records": {"$ref": "#/$defs/StringArray"},
                "total": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            ["map_id", "presentation_id"],
        ),
        "FiniteExpressionPayload": _object(
            {
                "expression_id": {"type": "string"},
                "text": {"type": "string"},
                "presentation_id": {"type": ["string", "null"]},
                "distinction_refs": {"$ref": "#/$defs/StringArray"},
                "record_refs": {"$ref": "#/$defs/StringArray"},
                "reason": {"type": "string"},
            },
            ["expression_id", "text"],
        ),
        "CertificatePayload": _object(
            {
                "certificate_id": {"type": "string"},
                "issuer": {"type": "string"},
                "scope": {"$ref": "#/$defs/JsonObject"},
                "issued_at": {"type": ["string", "null"], "format": "date-time"},
                "expires_at": {"type": ["string", "null"], "format": "date-time"},
                "metadata": {"$ref": "#/$defs/JsonObject"},
            },
            ["certificate_id", "issuer"],
        ),
        "CertificateTargetPayload": _object(
            {
                "target_id": {"type": "string"},
                "judgment_kind": {"type": "string", "enum": _enum(JudgmentKind)},
                "use_kind": {"type": "string", "enum": _enum(CertificateUseKind)},
                "target_node": {"type": "string"},
                "event_id": {"type": "string"},
                "target_state": {"type": "string", "enum": _enum(TargetState)},
                "scope": {"$ref": "#/$defs/JsonObject"},
                "required": {"type": "boolean"},
            },
            ["target_id", "judgment_kind", "use_kind", "target_node", "event_id"],
        ),
        "CertificateUsePayload": _object(
            {
                "use_id": {"type": "string"},
                "certificate_id": {"type": "string"},
                "target_id": {"type": "string"},
                "judgment_kind": {"type": "string", "enum": _enum(JudgmentKind)},
                "use_kind": {"type": "string", "enum": _enum(CertificateUseKind)},
                "target_node": {"type": "string"},
                "event_id": {"type": "string"},
                "state": {"type": "string", "enum": _enum(CertificateStateValue)},
            },
            ["use_id", "certificate_id", "target_id", "judgment_kind", "use_kind", "target_node"],
        ),
        "CertificateStatePayload": _object(
            {
                "state_id": {"type": "string"},
                "certificate_id": {"type": "string"},
                "target_id": {"type": "string"},
                "state": {"type": "string", "enum": _enum(CertificateStateValue)},
                "target_node": {"type": "string"},
                "reason": {"type": "string"},
            },
            ["state_id", "certificate_id", "target_id", "state", "target_node"],
        ),
        "RequirementPayload": _text_plus(
            {"empty_requirement_reason": {"type": ["string", "null"]}}
        ),
        "RequirementPolicyPayload": _object(
            {
                "policy_id": {"type": "string"},
                "process_id": {"type": "string"},
                "mode": {"type": "string"},
                "requirements": {"$ref": "#/$defs/StringArray"},
                "issue_ids": {"$ref": "#/$defs/StringArray"},
                "empty": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            ["policy_id"],
        ),
        "RequirementReasonPayload": _object(
            {
                "requirement_id": {"type": "string"},
                "source_policy_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            ["requirement_id"],
        ),
        "RequirementTransferPayload": _object(
            {
                "requirement_id": {"type": "string"},
                "from_mode": {"type": "string"},
                "to_mode": {"type": "string"},
                "accepted": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            ["requirement_id", "from_mode", "to_mode"],
        ),
        "IssuePayload": _text_plus(
            {
                "issue_id": {"type": "string"},
                "severity": {"type": "string", "enum": _enum(IssueSeverity)},
                "blocking": {"type": "boolean"},
                "resolved": {"type": "boolean"},
            }
        ),
        "ResiduePayload": _text_plus(
            {"distinction": {"type": "string"}, "mode_relevant": {"type": "boolean"}}
        ),
        "ObstructionPayload": _text_plus(
            {
                "kind": {"type": "string"},
                "mode": {"type": "string"},
                "scope": {"$ref": "#/$defs/JsonObject"},
                "blocks": {"$ref": "#/$defs/StringArray"},
                "critical": {"type": "boolean"},
            }
        ),
        "SettlednessDeclarationPayload": _object(
            {
                "distinction_id": {"type": "string"},
                "presentation_id": {"type": "string"},
                "declared_by": {"type": "string"},
                "reason": {"type": "string"},
            },
            ["distinction_id"],
        ),
        "SettlednessLicensePayload": _object(
            {
                "license_id": {"type": "string"},
                "distinction_id": {"type": "string"},
                "presentation_id": {"type": "string"},
                "licensed": {"type": "boolean"},
                "checker_record_id": {"type": "string"},
                "support_refs": {"$ref": "#/$defs/StringArray"},
                "reason": {"type": "string"},
            },
            ["license_id", "distinction_id"],
        ),
        "ObstructionProfilePayload": _object(
            {
                "profile_id": {"type": "string"},
                "obstruction_ids": {"$ref": "#/$defs/StringArray"},
                "critical_obstructions": {"$ref": "#/$defs/StringArray"},
                "discharged_obstructions": {"$ref": "#/$defs/StringArray"},
                "reason": {"type": "string"},
            },
            ["profile_id"],
        ),
        "UnavailableLeafPayload": _text_plus(
            {
                "node_id": {"type": "string"},
                "unavailable_policy": {"type": "string", "enum": _enum(UnavailablePolicy)},
                "evidence": {"const": False},
            }
        ),
        "ObligationPayload": _text_plus(
            {
                "obligation_id": {"type": "string"},
                "lifecycle": {"type": "string", "enum": _enum(ObligationLifecycle)},
                "hard": {"type": "boolean"},
                "owner": {"type": ["string", "null"]},
                "due_at": {"type": ["string", "null"], "format": "date-time"},
                "support_refs": {"$ref": "#/$defs/StringArray"},
            }
        ),
        "ObligationLifecyclePayload": _object(
            {
                "obligation_id": {"type": "string"},
                "source": {"type": "string", "enum": _enum(ObligationLifecycle)},
                "target": {"type": "string", "enum": _enum(ObligationLifecycle)},
                "event_id": {"type": "string"},
                "deadline_status": {"type": "string", "enum": _enum(DeadlineStatus)},
                "reason": {"type": "string"},
            },
            ["obligation_id", "source", "target"],
        ),
        "ObligationDischargePayload": _object(
            {
                "discharge_id": {"type": "string"},
                "obligation_id": {"type": "string"},
                "obstruction_id": {"type": "string"},
                "certificate_cover_id": {"type": "string"},
                "discharged": {"type": "boolean"},
                "support_refs": {"$ref": "#/$defs/StringArray"},
                "reason": {"type": "string"},
            },
            ["discharge_id", "obligation_id"],
        ),
        "EnvironmentTokenPayload": _text_plus(
            {
                "token_id": {"type": "string"},
                "kind": {"type": "string", "enum": _enum(EnvironmentTokenKind)},
                "name": {"type": "string"},
                "state": {"type": "string", "enum": _enum(TokenState)},
                "selected": {"type": "boolean"},
                "known_relevant": {"type": "boolean"},
                "freshness_at": {"type": ["string", "null"], "format": "date-time"},
                "scope": {"$ref": "#/$defs/JsonObject"},
            }
        ),
        "AcceptancePayload": _object(
            {
                "target_id": {"type": "string"},
                "accepted": {"type": "boolean"},
                "accepted_by": {"$ref": "#/$defs/StringArray"},
                "blocked_by": {"$ref": "#/$defs/StringArray"},
                "reason": {"type": "string"},
            },
            ["target_id"],
        ),
        "AbstentionPayload": _object(
            {
                "target_id": {"type": "string"},
                "abstained": {"type": "boolean"},
                "obstructed": {"type": "boolean"},
                "obstruction_refs": {"$ref": "#/$defs/StringArray"},
                "reason": {"type": "string"},
            },
            ["target_id"],
        ),
        "FailurePayload": _text_plus(
            {
                "failure_id": {"type": "string"},
                "mode": {"type": "string"},
                "relevant": {"type": "boolean"},
                "blocking": {"type": "boolean"},
                "resolved": {"type": "boolean"},
                "severity": {"type": "string", "enum": _enum(IssueSeverity)},
            }
        ),
        "ModeFilteredFailurePayload": _object(
            {
                "failure_id": {"type": "string"},
                "mode": {"type": "string"},
                "blocks": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            ["failure_id", "mode", "blocks"],
        ),
        "GateRequirementPayload": _object(
            {
                "impact_required": {"type": "boolean"},
                "selected_tokens": {"$ref": "#/$defs/StringArray"},
                "required_certificates": {"$ref": "#/$defs/StringArray"},
                "required_obligations": {"$ref": "#/$defs/StringArray"},
                "reason": {"type": "string"},
            },
            [],
        ),
        "GatePassPayload": _object(
            {
                "passed": {"type": "boolean"},
                "blocked_by": {"$ref": "#/$defs/StringArray"},
                "reason": {"type": "string"},
            },
            ["passed"],
        ),
        "ImpactPayload": _object(
            {
                "impact": {"type": "string", "enum": _enum(ImpactLevel)},
                "reason": {"type": "string"},
                "support_refs": {"$ref": "#/$defs/StringArray"},
            },
            ["impact"],
        ),
        "CriticCoveragePayload": _object(
            {
                "role": {"type": "string"},
                "covered": {"type": "boolean"},
                "waived": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            [],
        ),
        "ScopeExclusionPayload": _object(
            {
                "item": {"type": "string"},
                "disposition": {"type": "string"},
                "reason": {"type": "string"},
            },
            ["item", "disposition"],
        ),
        "ModeClosurePayload": _object(
            {
                "state": {"type": "string"},
                "reason": {"type": "string"},
                "transferred_to_obligation": {"type": ["string", "null"]},
            },
            [],
        ),
        "CompressionUsePayload": _object(
            {
                "sufficient": {"type": "boolean"},
                "reason": {"type": "string"},
                "scope": {"$ref": "#/$defs/JsonObject"},
            },
            ["sufficient"],
        ),
        "CompressionProfileClassPayload": _object(
            {
                "profile_class_id": {"type": "string"},
                "profiles": {"$ref": "#/$defs/StringArray"},
                "admissibility_by_profile": {"$ref": "#/$defs/JsonObject"},
                "compressed_values": {"$ref": "#/$defs/JsonObject"},
                "mode": {"type": "string"},
                "reason": {"type": "string"},
            },
            ["profile_class_id"],
        ),
        "CompressionFactorizationPayload": _object(
            {
                "factorization_id": {"type": "string"},
                "profile_class_id": {"type": "string"},
                "beta_by_value": {"$ref": "#/$defs/JsonObject"},
                "valid": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            ["factorization_id", "profile_class_id"],
        ),
        "ConsistencyProfilePayload": _object(
            {
                "profile_id": {"type": "string"},
                "passed": {"type": "boolean"},
                "support_coordinates": {"$ref": "#/$defs/StringArray"},
                "kernel_coordinates": {"$ref": "#/$defs/StringArray"},
                "certificate_coordinates": {"$ref": "#/$defs/StringArray"},
                "environment_coordinates": {"$ref": "#/$defs/StringArray"},
                "obligation_coordinates": {"$ref": "#/$defs/StringArray"},
                "provenance_coordinates": {"$ref": "#/$defs/StringArray"},
                "compression_coordinates": {"$ref": "#/$defs/StringArray"},
                "status_coordinates": {"$ref": "#/$defs/StringArray"},
                "admissibility_coordinates": {"$ref": "#/$defs/StringArray"},
                "missing_coordinates": {"$ref": "#/$defs/StringArray"},
                "failed_coordinates": {"$ref": "#/$defs/StringArray"},
                "reason": {"type": "string"},
            },
            ["profile_id"],
        ),
        "ValidatorTimeoutPayload": _object(
            {
                "validator_id": {"type": "string"},
                "timeout_ms": {"type": "integer"},
                "hidden": {"type": "boolean"},
                "blocks": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            ["validator_id", "timeout_ms"],
        ),
        "RootDebtPayload": _object(
            {
                "root_declaration_id": {"type": "string"},
                "text": {"type": "string"},
                "visible": {"type": "boolean"},
                "selected_as_obligation": {"type": "boolean"},
            },
            ["root_declaration_id", "text"],
        ),
        "KernelAdmissionPayload": _object(
            {
                "admission_id": {"type": "string"},
                "version_id": {"type": "string"},
                "kind": {"type": "string", "enum": _enum(KernelAdmissionKind)},
                "status": {"type": "string", "enum": _enum(KernelAdmissionStatus)},
                "basis_kind": {"type": "string", "enum": _enum(KernelAdmissionBasisKind)},
                "checker_version_id": {"type": "string"},
                "event_id": {"type": "string"},
                "basis_id": {"type": ["string", "null"]},
                "root_debt_id": {"type": ["string", "null"]},
                "reason": {"type": "string"},
                "metadata": {"$ref": "#/$defs/JsonObject"},
            },
            ["admission_id", "version_id", "kind", "status", "basis_kind", "checker_version_id"],
        ),
        "AnchorDeclarationPayload": _object(
            {
                "anchor_id": {"type": "string"},
                "target_id": {"type": "string"},
                "anchor_kind": {"type": "string", "enum": _enum(AnchorKind)},
                "event_id": {"type": "string"},
                "event_free": {"type": "boolean"},
                "provenance_ref": {"type": ["string", "null"]},
                "root_debt_id": {"type": ["string", "null"]},
                "permitted_roles": {"$ref": "#/$defs/StringArray"},
                "reason": {"type": "string"},
            },
            ["anchor_id", "target_id", "anchor_kind"],
        ),
        "AdequacyRecordPayload": _object(
            {
                "adequacy_id": {"type": "string"},
                "component": {"type": "string"},
                "state": {"type": "string", "enum": _enum(EvidenceState)},
                "disposition": {"type": "string", "enum": _enum(EvidenceDisposition)},
                "input_record_ids": {"$ref": "#/$defs/StringArray"},
                "issue_ids": {"$ref": "#/$defs/StringArray"},
                "obligation_ids": {"$ref": "#/$defs/StringArray"},
                "support_refs": {"$ref": "#/$defs/StringArray"},
                "checker_version_id": {"type": "string"},
                "rule_version_id": {"type": "string"},
                "mode": {"type": "string"},
                "waived": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            ["adequacy_id", "component", "state", "disposition"],
        ),
        "StatusBodyPayload": _object(
            {
                "body_id": {"type": "string"},
                "target_id": {"type": "string"},
                "support_coordinates": {"$ref": "#/$defs/StringArray"},
                "read_coordinates": {"$ref": "#/$defs/StringArray"},
                "respect_coordinates": {"$ref": "#/$defs/StringArray"},
                "checker_version_id": {"type": "string"},
                "rule_version_id": {"type": "string"},
                "reads_final_output": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            ["body_id", "target_id"],
        ),
        "CheckedStatusPayload": _object(
            {
                "status_id": {"type": "string"},
                "body_record_id": {"type": "string"},
                "status": {"type": "string", "enum": _enum(Status)},
                "checker_version_id": {"type": "string"},
                "rule_version_id": {"type": "string"},
                "read_coordinates": {"$ref": "#/$defs/StringArray"},
                "respect_coordinates": {"$ref": "#/$defs/StringArray"},
                "checked": {"type": "boolean"},
                "reads_final_output": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            ["status_id", "body_record_id", "status", "checker_version_id"],
        ),
        "PreAdmissibilitySupportVectorPayload": _object(
            {
                "vector_id": {"type": "string"},
                "target_id": {"type": "string"},
                "support_coordinates": {"$ref": "#/$defs/StringArray"},
                "validator_coordinates": {"$ref": "#/$defs/StringArray"},
                "kernel_coordinates": {"$ref": "#/$defs/StringArray"},
                "certificate_coordinates": {"$ref": "#/$defs/StringArray"},
                "environment_coordinates": {"$ref": "#/$defs/StringArray"},
                "obligation_coordinates": {"$ref": "#/$defs/StringArray"},
                "adequacy_coordinates": {"$ref": "#/$defs/StringArray"},
                "checker_version_id": {"type": "string"},
                "rule_version_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            ["vector_id", "target_id"],
        ),
        "AdmissibilityBodyPayload": _object(
            {
                "body_id": {"type": "string"},
                "target_id": {"type": "string"},
                "status_body_record_id": {"type": ["string", "null"]},
                "pre_admissibility_vector_id": {"type": ["string", "null"]},
                "support_coordinates": {"$ref": "#/$defs/StringArray"},
                "read_coordinates": {"$ref": "#/$defs/StringArray"},
                "respect_coordinates": {"$ref": "#/$defs/StringArray"},
                "checker_version_id": {"type": "string"},
                "rule_version_id": {"type": "string"},
                "reads_final_output": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            ["body_id", "target_id"],
        ),
        "CheckedAdmissibilityPayload": _object(
            {
                "admissibility_id": {"type": "string"},
                "body_record_id": {"type": "string"},
                "admissibility": {"type": "string", "enum": _enum(Admissibility)},
                "checker_version_id": {"type": "string"},
                "pre_admissibility_vector_id": {"type": "string"},
                "rule_version_id": {"type": "string"},
                "read_coordinates": {"$ref": "#/$defs/StringArray"},
                "respect_coordinates": {"$ref": "#/$defs/StringArray"},
                "checked": {"type": "boolean"},
                "reads_final_output": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            [
                "admissibility_id",
                "body_record_id",
                "admissibility",
                "checker_version_id",
                "pre_admissibility_vector_id",
            ],
        ),
        "NullCertificatePayload": _object(
            {
                "certificate_id": {"type": "string"},
                "target_id": {"type": "string"},
                "allowed": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            ["certificate_id", "target_id"],
        ),
        "CertificateCoverPayload": _object(
            {
                "cover_id": {"type": "string"},
                "obstruction_id": {"type": "string"},
                "certificate_id": {"type": "string"},
                "target_id": {"type": "string"},
                "discharged": {"type": "boolean"},
                "support_refs": {"$ref": "#/$defs/StringArray"},
                "reason": {"type": "string"},
            },
            ["cover_id", "obstruction_id", "certificate_id", "target_id"],
        ),
        "RespectCertificatePayload": _object(
            {
                "respect_id": {"type": "string"},
                "subject_record_id": {"type": "string"},
                "required_coordinates": {"$ref": "#/$defs/StringArray"},
                "respected_coordinates": {"$ref": "#/$defs/StringArray"},
                "valid": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            ["respect_id", "subject_record_id"],
        ),
        "RecordPreservingRefinementPayload": _object(
            {
                "transition_id": {"type": "string"},
                "before_record_ids": {"$ref": "#/$defs/StringArray"},
                "preserved_record_ids": {"$ref": "#/$defs/StringArray"},
                "archived_record_ids": {"$ref": "#/$defs/StringArray"},
                "provenance_edge_ids": {"$ref": "#/$defs/StringArray"},
                "reason": {"type": "string"},
            },
            ["transition_id"],
        ),
        "SelfModificationWitnessPayload": _object(
            {
                "witness_id": {"type": "string"},
                "previous_process_id": {"type": "string"},
                "next_process_id": {"type": "string"},
                "lineage_record_id": {"type": ["string", "null"]},
                "lineage_reason": {"type": "string"},
                "checker_version": {"type": "string"},
                "rule_version": {"type": "string"},
                "kernel_update_record_id": {"type": ["string", "null"]},
                "preserved_checks": {"$ref": "#/$defs/StringArray"},
                "replaced_checks": {"$ref": "#/$defs/StringArray"},
                "unavailable_checks": {"$ref": "#/$defs/StringArray"},
                "reason": {"type": "string"},
            },
            ["witness_id", "previous_process_id", "next_process_id"],
        ),
        "TheoryItemCoveragePayload": _object(
            {
                "item_id": {"type": "string"},
                "coverage": {"const": "implemented"},
                "runtime_anchor": {"type": "string"},
                "test_anchor": {"type": "string"},
                "reason": {"type": "string"},
                "anchor_refs": {"$ref": "#/$defs/JsonObject"},
            },
            ["item_id"],
        ),
        "StatusPayload": _object(
            {
                "status": {"type": "string", "enum": _enum(Status)},
                "body_record_id": {"type": ["string", "null"]},
                "checked": {"type": "boolean"},
                "read_coordinates": {"$ref": "#/$defs/StringArray"},
                "respect_coordinates": {"$ref": "#/$defs/StringArray"},
            },
            ["status"],
        ),
        "AdmissibilityPayload": _object(
            {
                "admissibility": {"type": "string", "enum": _enum(Admissibility)},
                "body_record_id": {"type": ["string", "null"]},
                "checked": {"type": "boolean"},
                "pre_admissibility_vector_id": {"type": ["string", "null"]},
                "read_coordinates": {"$ref": "#/$defs/StringArray"},
                "respect_coordinates": {"$ref": "#/$defs/StringArray"},
            },
            ["admissibility"],
        ),
        "TransitionWitnessPayload": _object(
            {
                "coordinate": {"type": "string"},
                "witness_record_id": {"type": "string"},
                "coordinate_kind": {
                    "type": ["string", "null"],
                    "enum": [*_enum(CoordinateKind), None],
                },
                "before_hash": {"type": ["string", "null"]},
                "after_hash": {"type": ["string", "null"]},
                "checker_version_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            ["coordinate", "witness_record_id"],
        ),
        "ValidationResultPayload": _object(
            {
                "status": {"type": "string", "enum": _enum(Status)},
                "admissibility": {"type": "string", "enum": _enum(Admissibility)},
                "summary": {"type": "string"},
                "records_checked": {"type": "integer"},
                "errors": {"$ref": "#/$defs/StringArray"},
                "warnings": {"$ref": "#/$defs/StringArray"},
            },
            ["status", "admissibility"],
        ),
    }


def _ledger_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": [
            "schema_version",
            "agent_id",
            "mode",
            "records",
            "support_graph",
            "event_order",
        ],
        "properties": {
            "schema_version": {"const": "2.0"},
            "agent_id": {"type": "string"},
            "mode": {"type": "string"},
            "records": {"type": "array", "items": {"$ref": "#/$defs/LedgerRecord"}},
            "support_graph": {"$ref": "#/$defs/SupportGraph"},
            "event_order": {"$ref": "#/$defs/EventOrder"},
            "provenance_edges": {
                "type": "array",
                "items": {"$ref": "#/$defs/ProvenanceEdge"},
            },
            "stage_builds": {"type": "array", "items": {"$ref": "#/$defs/StageBuildRecord"}},
            "frozen_stages": {"type": "array", "items": {"enum": _enum(LedgerStage)}},
            "metadata": {"$ref": "#/$defs/JsonObject"},
        },
        "additionalProperties": False,
    }


def _cut_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["schema_version", "cut_id", "created_at", "agent_id", "mode", "ledger"],
        "properties": {
            "schema_version": {"const": "2.0"},
            "cut_id": {"type": "string"},
            "created_at": {"type": "string", "format": "date-time"},
            "agent_id": {"type": "string"},
            "mode": {"type": "string"},
            "expression": {"type": ["string", "null"]},
            "output_ref": {"type": ["string", "null"]},
            "event_order": {"$ref": "#/$defs/EventOrder"},
            "validation_kernel": {"type": ["string", "null"]},
            "object_kernel": {"type": ["string", "null"]},
            "root_declarations": {"$ref": "#/$defs/StringArray"},
            "ledger": {"$ref": "#/$defs/EvaluatedLedger"},
            "support_graph": {"$ref": "#/$defs/SupportGraph"},
            "certificate_registry": {"$ref": "#/$defs/JsonObject"},
            "kernel": {"$ref": "#/$defs/JsonObject"},
            "environment_envelope": {"$ref": "#/$defs/JsonObject"},
            "theory_coverage": {"$ref": "#/$defs/JsonObject"},
            "process_class_registry": {"$ref": "#/$defs/JsonObject"},
            "presentation_basis": {"$ref": "#/$defs/JsonObject"},
            "requirement_policy": {"$ref": "#/$defs/JsonObject"},
            "settledness_licenses": {"$ref": "#/$defs/JsonObject"},
            "obstruction_profile": {"$ref": "#/$defs/JsonObject"},
            "compression_witness": {"$ref": "#/$defs/JsonObject"},
            "self_modification_witness": {"$ref": "#/$defs/JsonObject"},
            "provenance_edges": {
                "type": "array",
                "items": {"$ref": "#/$defs/ProvenanceEdge"},
            },
        },
        "additionalProperties": False,
    }


def _support_graph_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "nodes": {
                "type": "object",
                "additionalProperties": {"$ref": "#/$defs/LedgerRecord"},
            },
            "edges": {"type": "array", "items": {"$ref": "#/$defs/SupportEdge"}},
            "anchors": {"$ref": "#/$defs/StringArray"},
            "unavailable": {"type": "object", "additionalProperties": {"type": "string"}},
            "checked_nodes": {"$ref": "#/$defs/StringArray"},
            "frontier_items": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/FrontierItem"},
                },
            },
            "validation_coordinates": {
                "type": "object",
                "additionalProperties": {"$ref": "#/$defs/ValidationCoordinate"},
            },
            "anchor_roles": {
                "type": "object",
                "additionalProperties": {"type": "array", "items": {"enum": _enum(SupportRole)}},
            },
            "allow_cycles": {"type": "boolean"},
        },
        "additionalProperties": False,
    }


def _support_edge_schema() -> dict[str, Any]:
    return _object(
        {
            "source_id": {"type": "string"},
            "target_id": {"type": "string"},
            "role": {"type": "string", "enum": _enum(SupportRole)},
            "reason": {"type": "string"},
            "event_id": {"type": "string"},
            "witness_id": {"type": ["string", "null"]},
        },
        ["source_id", "target_id"],
    )


def _frontier_item_schema() -> dict[str, Any]:
    return _object(
        {
            "node_id": {"type": "string"},
            "role": {"type": "string", "enum": _enum(SupportRole)},
            "necessity": {"type": "string"},
            "unavailable_policy": {"type": "string", "enum": _enum(UnavailablePolicy)},
            "reason": {"type": "string"},
        },
        ["node_id", "role"],
    )


def _validation_coordinate_schema() -> dict[str, Any]:
    return _object(
        {
            "event_id": {"type": "string"},
            "stage": {"type": "string", "enum": _enum(LedgerStage)},
            "phase": {"type": "string", "enum": _enum(PhaseLevel)},
            "target_id": {"type": "string"},
        },
        ["event_id", "stage", "phase", "target_id"],
    )


def _event_order_schema() -> dict[str, Any]:
    return _object(
        {
            "current_event": {"type": "string"},
            "events": {"$ref": "#/$defs/StringArray"},
            "order_edges": {
                "type": "array",
                "items": {
                    "type": "array",
                    "prefixItems": [{"type": "string"}, {"type": "string"}],
                    "minItems": 2,
                    "maxItems": 2,
                },
            },
        },
        [],
    )


def _provenance_edge_schema() -> dict[str, Any]:
    return _object(
        {
            "source_id": {"type": "string"},
            "target_id": {"type": "string"},
            "relation": {"type": "string"},
            "event_id": {"type": "string"},
            "reason": {"type": "string"},
        },
        ["source_id", "target_id", "relation"],
    )


def _stage_build_schema() -> dict[str, Any]:
    return _object(
        {
            "build_id": {"type": "string"},
            "input_stage": {"type": "string", "enum": _enum(LedgerStage)},
            "output_stage": {"type": "string", "enum": _enum(LedgerStage)},
            "phase_start": {"type": "string", "enum": _enum(PhaseLevel)},
            "phase_end": {"type": "string", "enum": _enum(PhaseLevel)},
            "event_id": {"type": "string"},
            "rule_versions": {"$ref": "#/$defs/StringArray"},
            "checker_versions": {"$ref": "#/$defs/StringArray"},
            "input_frontier": {"$ref": "#/$defs/StringArray"},
            "emitted_records": {"$ref": "#/$defs/StringArray"},
            "reads": {"$ref": "#/$defs/StringArray"},
            "reason": {"type": "string"},
            "metadata": {"$ref": "#/$defs/JsonObject"},
        },
        ["build_id", "input_stage", "output_stage", "phase_start", "phase_end"],
    )


def _validation_result_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["status", "admissibility", "summary", "records_checked"],
        "properties": {
            "status": {"type": "string", "enum": _enum(Status)},
            "admissibility": {"type": "string", "enum": _enum(Admissibility)},
            "errors": {"type": "array", "items": {"$ref": "#/$defs/Problem"}},
            "warnings": {"type": "array", "items": {"$ref": "#/$defs/Problem"}},
            "issues": {"type": "array", "items": {"$ref": "#/$defs/LedgerRecord"}},
            "obligations": {"type": "array", "items": {"$ref": "#/$defs/LedgerRecord"}},
            "missing_support": {"type": "array", "items": {"$ref": "#/$defs/Problem"}},
            "certificate_problems": {"type": "array", "items": {"$ref": "#/$defs/Problem"}},
            "environment_problems": {"type": "array", "items": {"$ref": "#/$defs/Problem"}},
            "transition_problems": {"type": "array", "items": {"$ref": "#/$defs/Problem"}},
            "summary": {"type": "string"},
            "records_checked": {"type": "integer"},
        },
        "additionalProperties": False,
    }


def _transition_witness_schema() -> dict[str, Any]:
    return _object(
        {
            "coordinate": {"type": "string"},
            "witness_record_id": {"type": "string"},
            "reason": {"type": "string"},
        },
        ["coordinate", "witness_record_id"],
    )


def _transition_schema() -> dict[str, Any]:
    return _object(
        {
            "previous_cut_id": {"type": "string"},
            "next_cut_id": {"type": "string"},
            "changed_support_coordinates": {"$ref": "#/$defs/StringArray"},
            "changed_kernel_coordinates": {"$ref": "#/$defs/StringArray"},
            "changed_certificate_states": {"$ref": "#/$defs/StringArray"},
            "changed_obligations": {"$ref": "#/$defs/StringArray"},
            "changed_environment_tokens": {"$ref": "#/$defs/StringArray"},
            "changed_mode_or_scope": {"$ref": "#/$defs/StringArray"},
            "changed_provenance_coordinates": {"$ref": "#/$defs/StringArray"},
            "changed_event_order_coordinates": {"$ref": "#/$defs/StringArray"},
            "changed_status_admissibility_coordinates": {"$ref": "#/$defs/StringArray"},
            "witnesses": {"type": "array", "items": {"$ref": "#/$defs/TransitionWitness"}},
            "metadata": {"$ref": "#/$defs/JsonObject"},
        },
        ["previous_cut_id", "next_cut_id"],
    )


def _certificate_schema() -> dict[str, Any]:
    return _object(
        {
            "certificate_id": {"type": "string"},
            "issuer": {"type": "string"},
            "scope": {"$ref": "#/$defs/JsonObject"},
            "issued_at": {"type": "string", "format": "date-time"},
            "expires_at": {"type": ["string", "null"], "format": "date-time"},
            "metadata": {"$ref": "#/$defs/JsonObject"},
        },
        ["certificate_id", "issuer"],
    )


def _certificate_target_schema() -> dict[str, Any]:
    return _object(
        {
            "target_id": {"type": "string"},
            "judgment_kind": {"type": "string", "enum": _enum(JudgmentKind)},
            "use_kind": {"type": "string", "enum": _enum(CertificateUseKind)},
            "target_node": {"type": "string"},
            "event_id": {"type": "string"},
            "target_state": {"type": "string", "enum": _enum(TargetState)},
            "scope": {"$ref": "#/$defs/JsonObject"},
            "required": {"type": "boolean"},
            "metadata": {"$ref": "#/$defs/JsonObject"},
        },
        ["target_id", "judgment_kind", "use_kind", "target_node", "event_id"],
    )


def _required_certificate_schema() -> dict[str, Any]:
    return _object(
        {
            "target_id": {"type": "string"},
            "certificate_id": {"type": "string"},
            "required": {"type": "boolean"},
            "reason": {"type": "string"},
        },
        ["target_id", "certificate_id"],
    )


def _certificate_use_schema() -> dict[str, Any]:
    return _object(
        {
            "use_id": {"type": "string"},
            "certificate_id": {"type": "string"},
            "target_id": {"type": "string"},
            "judgment_kind": {"type": "string", "enum": _enum(JudgmentKind)},
            "use_kind": {"type": "string", "enum": _enum(CertificateUseKind)},
            "target_node": {"type": "string"},
            "event_id": {"type": "string"},
            "supports": {"$ref": "#/$defs/StringArray"},
            "metadata": {"$ref": "#/$defs/JsonObject"},
        },
        ["use_id", "certificate_id", "target_id", "judgment_kind", "use_kind", "target_node"],
    )


def _certificate_state_schema() -> dict[str, Any]:
    return _object(
        {
            "state_id": {"type": "string"},
            "certificate_id": {"type": "string"},
            "target_id": {"type": "string"},
            "state": {"type": "string", "enum": _enum(CertificateStateValue)},
            "target_node": {"type": "string"},
            "reason": {"type": "string"},
            "checked_at": {"type": "string", "format": "date-time"},
        },
        ["state_id", "certificate_id", "target_id", "state", "target_node"],
    )


def _certificate_registry_schema() -> dict[str, Any]:
    return _object(
        {
            "certificates": {"type": "array", "items": {"$ref": "#/$defs/Certificate"}},
            "targets": {"type": "array", "items": {"$ref": "#/$defs/CertificateTarget"}},
            "required": {
                "type": "array",
                "items": {"$ref": "#/$defs/RequiredCertificate"},
            },
            "uses": {"type": "array", "items": {"$ref": "#/$defs/CertificateUse"}},
            "states": {"type": "array", "items": {"$ref": "#/$defs/CertificateState"}},
        },
        [],
    )


def _kernel_admission_schema() -> dict[str, Any]:
    return _object(
        {
            "admission_id": {"type": "string"},
            "version_id": {"type": "string"},
            "kind": {"type": "string", "enum": _enum(KernelAdmissionKind)},
            "status": {"type": "string", "enum": _enum(KernelAdmissionStatus)},
            "basis_kind": {"type": "string", "enum": _enum(KernelAdmissionBasisKind)},
            "checker_version_id": {"type": "string"},
            "event_id": {"type": "string"},
            "basis_id": {"type": ["string", "null"]},
            "root_debt_id": {"type": ["string", "null"]},
            "reason": {"type": "string"},
            "metadata": {"$ref": "#/$defs/JsonObject"},
        },
        ["admission_id", "version_id", "kind", "status", "basis_kind", "checker_version_id"],
    )


def _kernel_schema() -> dict[str, Any]:
    return _object(
        {
            "kernel_id": {"type": "string"},
            "validation_kernel_id": {"type": "string"},
            "object_kernel_id": {"type": "string"},
            "root_declarations": {"type": "array", "items": {"$ref": "#/$defs/JsonObject"}},
            "admissions": {"type": "array", "items": {"$ref": "#/$defs/KernelAdmission"}},
            "root_debts": {"type": "array", "items": {"$ref": "#/$defs/JsonObject"}},
            "metadata": {"$ref": "#/$defs/JsonObject"},
        },
        ["kernel_id", "validation_kernel_id", "object_kernel_id"],
    )


def _problem_schema() -> dict[str, Any]:
    return _object(
        {
            "code": {"type": "string"},
            "message": {"type": "string"},
            "severity": {"type": "string", "enum": ["info", "warning", "error", "blocker"]},
            "related_record_ids": {"$ref": "#/$defs/StringArray"},
            "suggested_repair": {"type": ["string", "null"]},
        },
        ["code", "message"],
    )


def _text_plus(extra: dict[str, Any]) -> dict[str, Any]:
    properties = {
        "text": {"type": "string"},
        "reason": {"type": "string"},
        "metadata": {"$ref": "#/$defs/JsonObject"},
        **extra,
    }
    return _object(properties, ["text"])


def _object(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "required": required,
        "properties": properties,
        "additionalProperties": False,
    }


def _enum(enum_cls: type[Enum]) -> list[str]:
    return [str(item.value) for item in enum_cls]
