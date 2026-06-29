from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fost_agent_ledger.certificates import (
    Certificate,
    CertificateRegistry,
    CertificateState,
    CertificateTarget,
    CertificateUse,
    RequiredCertificate,
)
from fost_agent_ledger.enums import (
    CertificateStateValue,
    KernelAdmissionBasisKind,
    KernelAdmissionKind,
    KernelAdmissionStatus,
    LedgerStage,
    RecordType,
    SupportRole,
)
from fost_agent_ledger.kernels import Kernel, KernelAdmission, RootDebtRecord, validate_kernel
from fost_agent_ledger.model import LedgerRecord, SupportEdge
from fost_agent_ledger.support import SupportGraph


def _registry(*, expires_at: datetime | None = None) -> CertificateRegistry:
    cert = Certificate(
        certificate_id="cert-1",
        issuer="issuer",
        scope={"mode": "draft"},
        expires_at=expires_at or datetime.now(timezone.utc) + timedelta(days=1),
    )
    target = CertificateTarget(
        target_id="target-1",
        judgment_kind="policy",
        use_kind="cover",
        target_node="claim-1",
        event_id="event-0",
        scope={"mode": "draft"},
        required=True,
    )
    use = CertificateUse.create(
        certificate_id=cert.certificate_id,
        target_id=target.target_id,
        judgment_kind="policy",
        use_kind="cover",
        target_node="claim-1",
    )
    state = CertificateState(
        state_id="state-1",
        certificate_id=cert.certificate_id,
        target_id=target.target_id,
        state=CertificateStateValue.OK,
        target_node="claim-1",
    )
    return CertificateRegistry(
        certificates=(cert,),
        targets=(target,),
        required=(
            RequiredCertificate(
                target_id=target.target_id,
                certificate_id=cert.certificate_id,
            ),
        ),
        uses=(use,),
        states=(state,),
    )


def test_certificate_target_matching_passes_with_state_edge() -> None:
    target = LedgerRecord.create(RecordType.CLAIM, LedgerStage.CANDIDATE, {}, id="claim-1")
    state = LedgerRecord.create(
        RecordType.CERTIFICATE_STATE,
        LedgerStage.CHECKED_POLICY,
        {},
        id="state-1",
    )
    graph = (
        SupportGraph()
        .add_node(target)
        .add_node(state)
        .add_edge(
            SupportEdge(
                source_id="state-1",
                target_id="claim-1",
                role=SupportRole.COVER,
                witness_id="use-1",
            )
        )
    )
    assert _registry().validate(support_graph=graph) == ()


def test_missing_certificate_target_fails() -> None:
    registry = _registry()
    broken = CertificateRegistry(
        certificates=registry.certificates,
        targets=(),
        required=registry.required,
        uses=registry.uses,
        states=registry.states,
    )
    assert any(problem.code == "certificate.missing_target" for problem in broken.validate())


def test_expired_used_certificate_fails_but_unused_stale_does_not() -> None:
    expired = _registry(expires_at=datetime.now(timezone.utc) - timedelta(days=1))
    assert any(problem.code == "certificate.expired" for problem in expired.validate())
    stale_unused = CertificateRegistry(
        certificates=(
            Certificate(
                certificate_id="stale",
                issuer="issuer",
                expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            ),
        )
    )
    assert stale_unused.validate() == ()


def test_required_certificate_without_use_fails() -> None:
    registry = _registry()
    broken = CertificateRegistry(
        certificates=registry.certificates,
        targets=registry.targets,
        required=registry.required,
        uses=(),
        states=registry.states,
    )
    assert any(problem.code == "certificate.missing_required_use" for problem in broken.validate())


def test_kernel_self_certification_and_hidden_root_debt_fail() -> None:
    admission = KernelAdmission(
        admission_id="adm-1",
        version_id="checker-1",
        kind=KernelAdmissionKind.CHECKER,
        status=KernelAdmissionStatus.ADMITTED,
        basis_kind=KernelAdmissionBasisKind.SELF,
        checker_version_id="checker-1",
        root_debt_id="debt-1",
    )
    root_admission = KernelAdmission(
        admission_id="adm-2",
        version_id="rule-1",
        kind=KernelAdmissionKind.RULE,
        status=KernelAdmissionStatus.ADMITTED,
        basis_kind=KernelAdmissionBasisKind.ROOT,
        checker_version_id="checker-0",
        root_debt_id="debt-1",
    )
    kernel = Kernel(
        kernel_id="kernel",
        validation_kernel_id="k",
        object_kernel_id="k",
        admissions=(admission, root_admission),
        root_debts=(RootDebtRecord("debt-1", "root-1", "visible debt", visible=False),),
    )
    codes = {problem.code for problem in validate_kernel(kernel)}
    assert "kernel.validation_equals_object" in codes
    assert "kernel.self_certification" in codes
    assert "kernel.root_debt_hidden" in codes
