from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fost_agent_ledger import LedgerBuilder
from fost_agent_ledger.certificates import CertificateRegistry
from fost_agent_ledger.enums import CertificateUseKind, JudgmentKind, KernelAdmissionBasisKind
from fost_agent_ledger.kernels import Kernel
from fost_agent_ledger.ledger import EvaluatedLedger
from fost_agent_ledger.model import Problem
from fost_agent_ledger.policies import default_validate, get_default_mode_contract
from fost_agent_ledger.validators import (
    ValidatorFn,
    validate_admissibility,
    validate_certificate_targets,
    validate_contract_adequacy,
    validate_kernel_records,
    validate_phase_order,
    validate_status,
    validate_support_closure,
    validate_transition_records,
)


def test_validator_and_policy_wrappers() -> None:
    builder = LedgerBuilder(agent_id="agent-1", mode="draft")
    claim = builder.add_claim("Wrapped validators should run.")
    builder.add_support("Support.", supports=[claim.id])
    ledger = builder.finalize()

    def no_op_validator(checked: EvaluatedLedger) -> tuple[Problem, ...]:
        assert checked is ledger
        return ()

    validator: ValidatorFn = no_op_validator
    assert validator(ledger) == ()
    assert get_default_mode_contract("draft").name == "draft"
    assert default_validate(ledger).errors == ()
    assert validate_phase_order(ledger) == ()
    assert validate_support_closure(ledger) == ()
    assert validate_status(ledger) == ()
    assert validate_contract_adequacy(ledger) == ()
    assert validate_admissibility(ledger) == ()
    assert validate_certificate_targets(ledger, CertificateRegistry()) == ()
    assert validate_transition_records(ledger, ledger) == ()

    kernel = Kernel(
        kernel_id="kernel",
        validation_kernel_id="validation",
        object_kernel_id="object",
    )
    assert validate_kernel_records(kernel) == ()
    assert KernelAdmissionBasisKind.PRIOR_KERNEL.value == "prior_kernel"


def test_builder_extra_record_methods() -> None:
    builder = LedgerBuilder(agent_id="agent-1", mode="draft")
    claim = builder.add_claim("Extra builder methods are JSON serializable.")
    evidence = builder.add_evidence("Evidence.", supports=[claim.id])
    cert = builder.add_certificate(
        issuer="issuer",
        scope={"mode": "draft"},
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    target = builder.add_certificate_target(
        target_node=claim.id,
        judgment_kind=JudgmentKind.POLICY,
        use_kind=CertificateUseKind.COVER,
        required=True,
        scope={"mode": "draft"},
    )
    use, state = builder.add_certificate_use(
        certificate_id=cert.id,
        target_id=target.id,
        target_node=claim.id,
        judgment_kind=JudgmentKind.POLICY,
        use_kind=CertificateUseKind.COVER,
    )
    builder.add_environment_token(kind="tool_state", name="tool_state", selected=True)
    builder.add_impact("low")
    builder.add_scope_exclusion("x", disposition="excluded_supported")
    builder.add_mode_closure(state="pass")
    builder.add_compression_use(sufficient=True)
    ledger = builder.finalize()

    ids = {record.id for record in ledger.records}
    assert {claim.id, evidence.id, cert.id, target.id, use.id, state.id} <= ids
