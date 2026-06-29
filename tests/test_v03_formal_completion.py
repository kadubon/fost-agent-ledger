from __future__ import annotations

import json
from pathlib import Path

import pytest

from fost_agent_ledger import LedgerBuilder, validate_ledger
from fost_agent_ledger.cli import main
from fost_agent_ledger.enums import LedgerStage, RecordType, SupportRole
from fost_agent_ledger.ledger import EvaluatedLedger
from fost_agent_ledger.model import LedgerRecord, SupportEdge
from fost_agent_ledger.problem_codes import PROBLEM_EXPLANATIONS
from fost_agent_ledger.serialization import export_json_schema


def _codes(ledger: EvaluatedLedger) -> set[str]:
    return {problem.code for problem in validate_ledger(ledger).errors}


def test_v02_ledger_migrates_to_v10() -> None:
    v02 = {
        "schema_version": "0.2",
        "agent_id": "agent",
        "mode": "draft",
        "records": [],
        "support_graph": {},
        "event_order": {"events": ["event-0"], "order_edges": []},
        "provenance_edges": [],
        "stage_builds": [],
    }
    ledger = EvaluatedLedger.from_dict(v02)
    assert ledger.schema_version == "1.0"
    assert ledger.metadata["migrated_from_schema_version"] == "0.2"


def test_new_payloads_are_present_in_schema() -> None:
    defs = export_json_schema()["$defs"]
    for name in {
        "ObligationLifecyclePayload",
        "AcceptancePayload",
        "AbstentionPayload",
        "FailurePayload",
        "ModeFilteredFailurePayload",
        "ConsistencyProfilePayload",
        "ValidatorTimeoutPayload",
        "NullCertificatePayload",
        "RespectCertificatePayload",
        "LedgerTransition",
        "CertificateRegistry",
        "Kernel",
    }:
        assert name in defs


def test_obligation_lifecycle_conflict_and_invalid_transition() -> None:
    builder = LedgerBuilder(agent_id="agent", mode="draft")
    obligation = builder.add_obligation("Hard audit", hard=True)
    builder.add_obligation_lifecycle(
        obligation.id,
        source="discharged",
        target="active",
        event_id="event-1",
    )
    builder.add_obligation_lifecycle(
        obligation.id,
        source="active",
        target="failed",
        event_id="event-1",
    )
    codes = _codes(builder.ledger)
    assert "obligation.invalid_transition" in codes
    assert "obligation.lifecycle_conflict" in codes
    assert "obligation.hard_lifecycle_conflict" in codes


def test_failure_filtering_acceptance_abstention_and_timeout() -> None:
    builder = LedgerBuilder(agent_id="agent", mode="agent_action")
    claim = builder.add_claim("Act")
    builder.add_failure("Tool failed", mode="agent_action", blocking=True, resolved=False)
    builder.add_acceptance(claim.id, accepted=True, blocked_by=("failure-1",))
    builder.add_abstention(claim.id, obstructed=True, obstruction_refs=("obs-1",))
    builder.add_validator_timeout("policy-check", timeout_ms=1000, hidden=True)
    codes = _codes(builder.ledger)
    assert "failure.mode_relevant_blocks" in codes
    assert "acceptance.blocked" in codes
    assert "abstention.obstructed" in codes
    assert "validator.timeout" in codes
    assert "validator.timeout_hidden" in codes


def test_mode_irrelevant_failure_does_not_block() -> None:
    builder = LedgerBuilder(agent_id="agent", mode="draft")
    claim = builder.add_claim("Draft")
    builder.add_support("Support", supports=[claim.id])
    builder.add_failure("Publication-only failure", mode="publication", blocking=True)
    codes = _codes(builder.finalize())
    assert "failure.mode_relevant_blocks" not in codes


def test_consistency_profile_null_certificate_and_respect_certificate() -> None:
    builder = LedgerBuilder(agent_id="agent", mode="draft")
    claim = builder.add_claim("Claim")
    builder.add_consistency_profile(
        "profile-1",
        passed=False,
        missing_coordinates=("support:claim",),
        failed_coordinates=("kernel:checker",),
    )
    builder.add_null_certificate(certificate_id="null-cert", target_id=claim.id)
    builder.add_respect_certificate(
        respect_id="respect-1",
        subject_record_id=claim.id,
        required_coordinates=("status:body", "admissibility:body"),
        respected_coordinates=("status:body",),
    )
    codes = _codes(builder.ledger)
    assert "consistency.profile_incomplete" in codes
    assert "certificate.null_misuse" in codes
    assert "respect.missing_coordinates" in codes


def test_finality_respect_and_output_leakage() -> None:
    status = LedgerRecord.create(
        RecordType.STATUS,
        LedgerStage.CHECKED_STATUS,
        {
            "status": "supported",
            "checked": False,
            "respect_coordinates": ["status:body"],
            "reads_final_output": True,
        },
        id="status",
    )
    admissibility = LedgerRecord.create(
        RecordType.ADMISSIBILITY,
        LedgerStage.CHECKED_ADMISSIBILITY,
        {
            "admissibility": "admissible",
            "body_record_id": "status",
            "respect_coordinates": [],
        },
        id="admissibility",
    )
    ledger = EvaluatedLedger(agent_id="agent", mode="draft").add_records((status, admissibility))
    codes = _codes(ledger)
    assert "admissibility.unchecked_status_license" in codes
    assert "respect.status_admissibility_mismatch" in codes
    assert "finality.output_leakage" in codes


def test_gate_policy_environment_and_certificate_cycles() -> None:
    gate_req = LedgerRecord.create(
        RecordType.GATE_REQUIREMENT,
        LedgerStage.CHECKED_POLICY,
        {"required_obligations": ["missing-obligation"]},
        id="gate-req",
    )
    gate_pass = LedgerRecord.create(
        RecordType.GATE_PASS,
        LedgerStage.CHECKED_POLICY,
        {"passed": True},
        id="gate-pass",
    )
    env = LedgerRecord.create(
        RecordType.ENVIRONMENT_TOKEN,
        LedgerStage.CHECKED_POLICY,
        {"text": "policy version", "kind": "policy_version", "name": "policy", "selected": True},
        id="env",
    )
    obligation = LedgerRecord.create(
        RecordType.OBLIGATION,
        LedgerStage.CHECKED_POLICY,
        {"text": "obligation", "obligation_id": "obl"},
        id="obl",
    )
    cert = LedgerRecord.create(RecordType.CERTIFICATE, LedgerStage.CHECKED_POLICY, {}, id="cert")
    kernel = LedgerRecord.create(
        RecordType.KERNEL_ADMISSION,
        LedgerStage.CHECKED_POLICY,
        {
            "admission_id": "adm",
            "version_id": "kernel",
            "kind": "rule",
            "status": "admitted",
            "basis_kind": "external_certificate",
            "checker_version_id": "checker",
            "basis_id": "cert",
        },
        id="kernel",
    )
    graph_ledger = EvaluatedLedger(agent_id="agent", mode="draft").add_records(
        (gate_req, gate_pass, env, obligation, cert, kernel)
    )
    for source, target, role in (
        ("gate-req", "gate-pass", SupportRole.GATE_REQUIREMENT),
        ("gate-pass", "gate-req", SupportRole.GATE_PASS),
        ("env", "obl", SupportRole.ENVIRONMENT),
        ("obl", "env", SupportRole.OBLIGATION_LIFECYCLE),
        ("cert", "kernel", SupportRole.KERNEL_ADMISSION),
        ("kernel", "cert", SupportRole.KERNEL_ADMISSION),
    ):
        graph_ledger = graph_ledger.add_support_edge(
            SupportEdge(source_id=source, target_id=target, role=role, witness_id=source)
        )
    codes = _codes(graph_ledger)
    assert "policy.generated_obligation_omission" in codes
    assert "gate.cycle" in codes
    assert "environment.policy_generation_cycle" in codes
    assert "certificate.kernel_circular_support" in codes
    assert "certificate.support_cycle" in codes


def test_certificate_role_stage_and_cover_type_confusion() -> None:
    claim = LedgerRecord.create(RecordType.CLAIM, LedgerStage.CANDIDATE, {"text": "x"}, id="c")
    obligation = LedgerRecord.create(
        RecordType.OBLIGATION,
        LedgerStage.CHECKED_POLICY,
        {"text": "done", "obligation_id": "o", "lifecycle": "discharged"},
        id="o",
    )
    target_claim = LedgerRecord.create(
        RecordType.CERTIFICATE_TARGET,
        LedgerStage.CHECKED_POLICY,
        {
            "target_id": "target-c",
            "judgment_kind": "policy",
            "use_kind": "cover",
            "target_node": "c",
            "event_id": "event-0",
        },
        id="target-c",
    )
    target_obligation = LedgerRecord.create(
        RecordType.CERTIFICATE_TARGET,
        LedgerStage.CHECKED_POLICY,
        {
            "target_id": "target-o",
            "judgment_kind": "policy",
            "use_kind": "cover",
            "target_node": "o",
            "event_id": "event-0",
        },
        id="target-o",
    )
    ledger = EvaluatedLedger(agent_id="agent", mode="draft").add_records(
        (claim, obligation, target_claim, target_obligation)
    )
    codes = _codes(ledger)
    assert "certificate.role_stage_violation" in codes
    assert "certificate.cover_check_type_confusion" in codes


def test_evidence_failure_laundering_is_rejected() -> None:
    evidence = LedgerRecord.create(
        RecordType.EVIDENCE,
        LedgerStage.SUPPORT,
        {"text": "bad evidence", "state": "fail", "disposition": "blocked"},
        id="evidence",
    )
    obligation = LedgerRecord.create(
        RecordType.OBLIGATION,
        LedgerStage.CHECKED_POLICY,
        {"text": "follow up", "obligation_id": "obl", "support_refs": ["evidence"]},
        id="obl",
    )
    ledger = EvaluatedLedger(agent_id="agent", mode="draft").add_records((evidence, obligation))
    assert "evidence.failure_laundering" in _codes(ledger)


def test_cli_explain_and_init(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["explain", "validator.timeout"]) == 0
    explained = json.loads(capsys.readouterr().out)
    assert explained["code"] == "validator.timeout"
    assert "repair" in explained

    assert main(["explain", "unknown.code"]) == 1
    assert "unknown problem code" in capsys.readouterr().out

    assert main(["init", "--mode", "draft", "--agent-id", "agent-x"]) == 0
    initialized = json.loads(capsys.readouterr().out)
    assert initialized["schema_version"] == "1.0"
    assert initialized["agent_id"] == "agent-x"
    assert {record["record_type"] for record in initialized["records"]} >= {
        "process_class",
        "distinction_basis",
        "finite_presentation",
        "presentation_map",
        "finite_expression",
        "requirement_policy",
    }


def test_problem_catalog_has_docs_entries() -> None:
    docs = Path("docs/problem_codes.md")
    if docs.exists():
        text = docs.read_text(encoding="utf-8")
        for code in PROBLEM_EXPLANATIONS:
            assert code in text
