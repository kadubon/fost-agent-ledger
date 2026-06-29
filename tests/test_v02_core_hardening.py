from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fost_agent_ledger import LedgerBuilder, OperationalCut, validate_ledger
from fost_agent_ledger.certificates import (
    Certificate,
    CertificateRegistry,
    CertificateState,
    CertificateTarget,
    CertificateUse,
    RequiredCertificate,
)
from fost_agent_ledger.enums import (
    Admissibility,
    CertificateStateValue,
    KernelAdmissionBasisKind,
    KernelAdmissionKind,
    KernelAdmissionStatus,
    LedgerStage,
    PhaseLevel,
    RecordType,
    Status,
    TargetState,
)
from fost_agent_ledger.finality import (
    AdmissibilityBody,
    CheckedAdmissibility,
    CheckedStatus,
    PreAdmissibilitySupportVector,
    RespectRecord,
    StatusBody,
)
from fost_agent_ledger.kernels import Kernel, KernelAdmission, validate_kernel
from fost_agent_ledger.ledger import EvaluatedLedger
from fost_agent_ledger.model import LedgerRecord, SupportEdge
from fost_agent_ledger.serialization import export_json_schema
from fost_agent_ledger.stages import StageBuildRecord, ValidationCoordinate
from fost_agent_ledger.support import SupportGraph
from fost_agent_ledger.transitions import TransitionWitness, diff_ledgers, validate_transition


def test_v01_ledger_migrates_to_v10_and_roundtrips() -> None:
    legacy = {
        "agent_id": "agent-1",
        "mode": "draft",
        "records": [
            LedgerRecord.create(
                RecordType.CLAIM,
                LedgerStage.CANDIDATE,
                {"text": "legacy", "extra": "ignored"},
                id="claim-1",
            ).to_dict()
        ],
        "support_graph": {},
    }
    ledger = EvaluatedLedger.from_dict(legacy)
    assert ledger.schema_version == "1.0"
    assert ledger.metadata["migrated_from_schema_version"] == "0.1"

    roundtripped = EvaluatedLedger.from_dict(ledger.to_dict())
    assert roundtripped.to_dict() == ledger.to_dict()


def test_json_schema_has_typed_payload_and_cut_defs() -> None:
    schema = export_json_schema()
    defs = schema["$defs"]
    assert defs["EvaluatedLedger"]["properties"]["schema_version"]["const"] == "1.0"
    assert "OperationalCut" in defs
    assert "LedgerTransition" in defs
    assert "CertificateRegistry" in defs
    assert "Kernel" in defs
    assert "CertificateTargetPayload" in defs
    assert defs["UnavailableLeafPayload"]["properties"]["evidence"]["const"] is False

    cut = OperationalCut.create(agent_id="agent", mode="draft")
    assert cut.ledger["schema_version"] == "1.0"
    assert cut.event_order["current_event"] == "event-0"


def test_stage_build_rejects_future_read_and_emitted_stage_mismatch() -> None:
    claim = LedgerRecord.create(RecordType.CLAIM, LedgerStage.CANDIDATE, {"text": "claim"}, id="c")
    status = LedgerRecord.create(
        RecordType.STATUS,
        LedgerStage.CHECKED_STATUS,
        {"status": Status.SUPPORTED.value},
        id="s",
    )
    build = StageBuildRecord(
        build_id="build-1",
        input_stage=LedgerStage.CANDIDATE,
        output_stage=LedgerStage.CHECKED_POLICY,
        phase_start=PhaseLevel.POLICY_SELECTION,
        phase_end=PhaseLevel.POLICY_GATE_PASS_ISSUE,
        emitted_records=("c",),
        reads=("s",),
    )
    ledger = EvaluatedLedger(agent_id="agent", mode="draft").add_records((claim, status))
    result = validate_ledger(ledger.add_stage_build(build))
    codes = {problem.code for problem in result.errors}
    assert "stage.emitted_stage_mismatch" in codes
    assert "stage.forbidden_future_read" in codes


def test_support_order_same_target_same_phase_is_rejected() -> None:
    source = LedgerRecord.create(RecordType.SUPPORT, LedgerStage.SUPPORT, {"text": "a"}, id="a")
    target = LedgerRecord.create(RecordType.SUPPORT, LedgerStage.SUPPORT, {"text": "b"}, id="b")
    coordinate = ValidationCoordinate(
        event_id="event-0",
        stage=LedgerStage.SUPPORT,
        phase=PhaseLevel.SUPPORT,
        target_id="target-1",
    )
    graph = (
        SupportGraph()
        .add_node(source)
        .add_node(target)
        .add_validation_coordinate("a", coordinate)
        .add_validation_coordinate("b", coordinate)
        .add_edge(SupportEdge(source_id="a", target_id="b", witness_id="a"))
    )
    codes = {problem.code for problem in graph.validate()}
    assert "support.order_violation" in codes
    assert "support.same_target_same_phase" in codes


def test_unavailable_leaf_payload_cannot_claim_evidence() -> None:
    record = LedgerRecord.create(
        RecordType.UNAVAILABLE_LEAF,
        LedgerStage.SUPPORT,
        {"text": "missing", "evidence": True},
        id="missing",
    )
    result = validate_ledger(EvaluatedLedger(agent_id="agent", mode="draft").add_record(record))
    assert any(problem.code == "unavailable.evidence_misuse" for problem in result.errors)


def test_certificate_target_state_and_transition_only_defaults() -> None:
    cert = Certificate(
        certificate_id="cert",
        issuer="issuer",
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    transition_target = CertificateTarget(
        target_id="transition-target",
        judgment_kind="transition",
        use_kind="transition",
        target_node="node",
        event_id="event-0",
        required=True,
        target_state=TargetState.MISSING_TARGET,
    )
    transition_use = CertificateUse.create(
        certificate_id="cert",
        target_id="transition-target",
        judgment_kind="transition",
        use_kind="transition",
        target_node="node",
    )
    transition_state = CertificateState(
        state_id="state",
        certificate_id="cert",
        target_id="transition-target",
        state=CertificateStateValue.STALE,
        target_node="node",
    )
    registry = CertificateRegistry(
        certificates=(cert,),
        targets=(transition_target,),
        required=(RequiredCertificate("transition-target", "cert"),),
        uses=(transition_use,),
        states=(transition_state,),
    )
    assert registry.validate() == ()
    assert registry.validate(include_transition_targets=True)


def test_kernel_prior_and_external_admissions_require_basis_witnesses() -> None:
    missing = Kernel(
        kernel_id="kernel",
        validation_kernel_id="validation",
        object_kernel_id="object",
        admissions=(
            KernelAdmission(
                admission_id="prior",
                version_id="rule-1",
                kind=KernelAdmissionKind.RULE,
                status=KernelAdmissionStatus.ADMITTED,
                basis_kind=KernelAdmissionBasisKind.PRIOR_KERNEL,
                checker_version_id="checker-1",
            ),
            KernelAdmission(
                admission_id="external",
                version_id="checker-2",
                kind=KernelAdmissionKind.CHECKER,
                status=KernelAdmissionStatus.ADMITTED,
                basis_kind=KernelAdmissionBasisKind.EXTERNAL_CERTIFICATE,
                checker_version_id="checker-1",
            ),
        ),
    )
    codes = {problem.code for problem in validate_kernel(missing)}
    assert "kernel.missing_prior_kernel_witness" in codes
    assert "kernel.missing_external_certificate_anchor" in codes

    witnessed = Kernel(
        kernel_id="kernel",
        validation_kernel_id="validation",
        object_kernel_id="object",
        admissions=(
            KernelAdmission(
                admission_id="prior",
                version_id="rule-1",
                kind=KernelAdmissionKind.RULE,
                status=KernelAdmissionStatus.ADMITTED,
                basis_kind=KernelAdmissionBasisKind.PRIOR_KERNEL,
                checker_version_id="checker-1",
                basis_id="kernel-0",
            ),
        ),
    )
    assert validate_kernel(witnessed) == ()


def test_status_admissibility_separation_and_finality_models() -> None:
    status = LedgerRecord.create(
        RecordType.STATUS,
        LedgerStage.CHECKED_STATUS,
        {"status": Status.SUPPORTED.value},
        id="status",
    )
    admissibility = LedgerRecord.create(
        RecordType.ADMISSIBILITY,
        LedgerStage.CHECKED_ADMISSIBILITY,
        {"admissibility": Admissibility.ADMISSIBLE.value, "body_record_id": "status"},
        id="adm",
    )
    ledger = EvaluatedLedger(agent_id="agent", mode="draft").add_records((status, admissibility))
    result = validate_ledger(ledger)
    assert any(problem.code == "admissibility.checked_status_leakage" for problem in result.errors)

    assert StatusBody.from_dict({"body_id": "b", "target_id": "t"}).target_id == "t"
    assert (
        CheckedStatus.from_dict(
            {
                "status_id": "s",
                "body_record_id": "b",
                "status": "supported",
                "checker_version_id": "checker",
            }
        ).status
        == Status.SUPPORTED
    )
    assert AdmissibilityBody.from_dict({"body_id": "ab", "target_id": "t"}).body_id == "ab"
    assert (
        CheckedAdmissibility.from_dict(
            {
                "admissibility_id": "a",
                "body_record_id": "ab",
                "admissibility": "admissible",
                "checker_version_id": "checker",
                "pre_admissibility_vector_id": "v",
            }
        ).admissibility
        == Admissibility.ADMISSIBLE
    )
    assert RespectRecord.from_dict(
        {"respect_id": "r", "coordinate": "c", "respected": True}
    ).respected
    assert PreAdmissibilitySupportVector.from_dict({"vector_id": "v"}).vector_id == "v"


def test_transition_diff_detects_same_id_change_and_witnessed_gain() -> None:
    before_record = LedgerRecord.create(
        RecordType.CLAIM,
        LedgerStage.CANDIDATE,
        {"text": "old"},
        id="claim",
    )
    after_record = LedgerRecord.create(
        RecordType.CLAIM,
        LedgerStage.CANDIDATE,
        {"text": "new"},
        id="claim",
    )
    before = EvaluatedLedger(agent_id="agent", mode="draft").add_record(before_record)
    after = EvaluatedLedger(agent_id="agent", mode="draft").add_record(after_record)
    assert "claim" in diff_ledgers(before, after).changed_support_coordinates

    unsupported_builder = LedgerBuilder(agent_id="agent", mode="draft")
    unsupported_builder.add_claim("claim")
    unsupported = unsupported_builder.finalize()
    supported_builder = LedgerBuilder(agent_id="agent", mode="draft")
    supported_claim = supported_builder.add_claim("claim")
    support = supported_builder.add_support("support", supports=[supported_claim.id])
    supported = supported_builder.finalize()
    transition = diff_ledgers(unsupported, supported)
    witnessed = transition.__class__(
        previous_cut_id=transition.previous_cut_id,
        next_cut_id=transition.next_cut_id,
        changed_support_coordinates=transition.changed_support_coordinates,
        changed_kernel_coordinates=transition.changed_kernel_coordinates,
        changed_certificate_states=transition.changed_certificate_states,
        changed_obligations=transition.changed_obligations,
        changed_environment_tokens=transition.changed_environment_tokens,
        changed_mode_or_scope=transition.changed_mode_or_scope,
        changed_provenance_coordinates=transition.changed_provenance_coordinates,
        changed_event_order_coordinates=transition.changed_event_order_coordinates,
        changed_status_admissibility_coordinates=(
            transition.changed_status_admissibility_coordinates
        ),
        witnesses=tuple(
            TransitionWitness(coordinate=coordinate, witness_record_id=support.id)
            for coordinate in transition.changed_coordinates
        ),
    )
    codes = {problem.code for problem in validate_transition(unsupported, supported, witnessed)}
    assert "transition.untraced_admissibility_gain" not in codes
    assert "transition.missing_witness" not in codes
