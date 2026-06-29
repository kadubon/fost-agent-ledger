from __future__ import annotations

import json

import pytest

from fost_agent_ledger import LedgerBuilder, validate_ledger
from fost_agent_ledger.cli import main
from fost_agent_ledger.enums import LedgerStage, RecordType
from fost_agent_ledger.ledger import EvaluatedLedger
from fost_agent_ledger.model import LedgerRecord
from fost_agent_ledger.serialization import export_json_schema


def _codes(ledger: EvaluatedLedger) -> set[str]:
    return {problem.code for problem in validate_ledger(ledger).errors}


def test_v03_ledger_migrates_to_v10_roundtrip() -> None:
    v03 = {
        "schema_version": "0.3",
        "agent_id": "agent",
        "mode": "draft",
        "records": [],
        "support_graph": {},
        "event_order": {"events": ["event-0"], "order_edges": []},
        "provenance_edges": [],
        "stage_builds": [],
    }
    ledger = EvaluatedLedger.from_dict(v03)
    assert ledger.schema_version == "1.0"
    assert ledger.metadata["migrated_from_schema_version"] == "0.3"
    assert EvaluatedLedger.from_json(ledger.to_json()).to_dict() == ledger.to_dict()


def test_v04_ledger_migrates_to_v10_roundtrip() -> None:
    v04 = {
        "schema_version": "0.4",
        "agent_id": "agent",
        "mode": "research_summary",
        "records": [],
        "support_graph": {},
        "event_order": {"events": ["event-0"], "order_edges": []},
        "provenance_edges": [],
        "stage_builds": [],
    }
    ledger = EvaluatedLedger.from_dict(v04)
    assert ledger.schema_version == "1.0"
    assert ledger.metadata["migrated_from_schema_version"] == "0.4"
    assert EvaluatedLedger.from_json(ledger.to_json()).to_dict() == ledger.to_dict()


def test_v10_payloads_are_present_in_schema() -> None:
    defs = export_json_schema()["$defs"]
    for name in {
        "ProcessClassPayload",
        "DistinctionBasisPayload",
        "FinitePresentationPayload",
        "PresentationMapPayload",
        "FiniteExpressionPayload",
        "RequirementPolicyPayload",
        "RequirementReasonPayload",
        "RequirementTransferPayload",
        "SettlednessDeclarationPayload",
        "SettlednessLicensePayload",
        "ObstructionProfilePayload",
        "CertificateCoverPayload",
        "ObligationDischargePayload",
        "CompressionProfileClassPayload",
        "CompressionFactorizationPayload",
        "RecordPreservingRefinementPayload",
        "SelfModificationWitnessPayload",
        "TheoryItemCoveragePayload",
    }:
        assert name in defs


def test_process_presentation_and_requirement_countermodels() -> None:
    records = (
        LedgerRecord.create(
            RecordType.DISTINCTION_BASIS,
            LedgerStage.CANDIDATE,
            {"basis_id": "basis", "distinctions": ["a"]},
            id="basis",
        ),
        LedgerRecord.create(
            RecordType.FINITE_PRESENTATION,
            LedgerStage.CANDIDATE,
            {
                "presentation_id": "presentation",
                "basis_id": "basis",
                "expression_id": "missing-expression",
                "distinction_ids": ["a", "b"],
            },
            id="presentation",
        ),
        LedgerRecord.create(
            RecordType.FINITE_EXPRESSION,
            LedgerStage.CANDIDATE,
            {
                "expression_id": "expr",
                "text": "x",
                "presentation_id": "presentation",
                "distinction_refs": ["outside"],
            },
            id="expr",
        ),
        LedgerRecord.create(
            RecordType.PRESENTATION_MAP,
            LedgerStage.CHECKED_CORE,
            {
                "map_id": "map",
                "presentation_id": "presentation",
                "domain_distinctions": ["a"],
                "total": True,
            },
            id="map",
        ),
        LedgerRecord.create(
            RecordType.REQUIREMENT,
            LedgerStage.CHECKED_CORE,
            {"text": "needs reason"},
            id="req",
        ),
        LedgerRecord.create(
            RecordType.REQUIREMENT_POLICY,
            LedgerStage.CHECKED_CORE,
            {
                "policy_id": "policy",
                "process_id": "missing-process",
                "requirements": ["req"],
                "issue_ids": ["missing-issue"],
            },
            id="policy",
        ),
        LedgerRecord.create(
            RecordType.REQUIREMENT_TRANSFER,
            LedgerStage.CHECKED_CORE,
            {"requirement_id": "req", "from_mode": "draft", "to_mode": "publication"},
            id="transfer",
        ),
    )
    ledger = EvaluatedLedger(agent_id="agent", mode="draft").add_records(records)
    codes = _codes(ledger)
    assert "process_class.missing_registry" in codes
    assert "presentation.unmapped_distinction" in codes
    assert "presentation.expression_outside_scope" in codes
    assert "requirement.missing_reason" in codes
    assert "requirement.missing_transfer_reason" in codes
    assert "requirement.unanswered_issue" in codes


def test_settledness_obstruction_cover_and_discharge_countermodels() -> None:
    records = (
        LedgerRecord.create(
            RecordType.SETTLEDNESS_DECLARATION,
            LedgerStage.CHECKED_CORE,
            {"distinction_id": "d"},
            id="decl",
        ),
        LedgerRecord.create(
            RecordType.SETTLEDNESS_LICENSE,
            LedgerStage.CHECKED_CORE,
            {"license_id": "lic", "distinction_id": "e", "support_refs": ["lic"]},
            id="lic",
        ),
        LedgerRecord.create(
            RecordType.OBSTRUCTION,
            LedgerStage.CHECKED_CORE,
            {"text": "critical obstruction", "critical": True},
            id="obs",
        ),
        LedgerRecord.create(
            RecordType.OBSTRUCTION_PROFILE,
            LedgerStage.CHECKED_CORE,
            {"profile_id": "obs-profile", "critical_obstructions": ["obs"]},
            id="obs-profile",
        ),
        LedgerRecord.create(
            RecordType.CERTIFICATE_COVER,
            LedgerStage.CHECKED_POLICY,
            {
                "cover_id": "cover",
                "obstruction_id": "obs",
                "certificate_id": "cert",
                "target_id": "target",
                "support_refs": ["cover"],
            },
            id="cover",
        ),
        LedgerRecord.create(
            RecordType.OBLIGATION_DISCHARGE,
            LedgerStage.CHECKED_POLICY,
            {"discharge_id": "dis", "obligation_id": "obl", "support_refs": ["dis"]},
            id="dis",
        ),
    )
    ledger = EvaluatedLedger(agent_id="agent", mode="draft").add_records(records)
    codes = _codes(ledger)
    assert "settledness.unlicensed" in codes
    assert "settledness.license_cycle" in codes
    assert "obstruction.critical_undischarged" in codes
    assert "certificate.cover_cycle" in codes
    assert "obligation.discharge_cycle" in codes


def test_refinement_self_modification_and_compression_countermodels() -> None:
    records = (
        LedgerRecord.create(
            RecordType.RECORD_PRESERVING_REFINEMENT,
            LedgerStage.TRANSITION,
            {"transition_id": "transition", "before_record_ids": ["lost-record"]},
            id="transition",
        ),
        LedgerRecord.create(
            RecordType.SELF_MODIFICATION_WITNESS,
            LedgerStage.TRANSITION,
            {
                "witness_id": "selfmod",
                "previous_process_id": "p0",
                "next_process_id": "p1",
            },
            id="selfmod",
        ),
        LedgerRecord.create(
            RecordType.COMPRESSION_PROFILE_CLASS,
            LedgerStage.TRANSITION,
            {
                "profile_class_id": "class",
                "profiles": ["p1", "p2"],
                "admissibility_by_profile": {"p1": True, "p2": False},
                "compressed_values": {"p1": "same", "p2": "same"},
            },
            id="class",
        ),
    )
    ledger = EvaluatedLedger(agent_id="agent", mode="self_modification").add_records(records)
    codes = _codes(ledger)
    assert "transition.record_not_preserved" in codes
    assert "self_modification.missing_lineage" in codes
    assert "self_modification.missing_rule_disclosure" in codes
    assert "compression.exactness_violation" in codes
    assert "compression.factorization_missing" in codes


def test_valid_compression_factorization_passes() -> None:
    builder = LedgerBuilder(agent_id="agent", mode="draft")
    claim = builder.add_claim("Compressed profiles preserve admissibility.")
    builder.add_support("Support", supports=[claim.id])
    builder.add_compression_profile_class(
        profile_class_id="class",
        profiles=("p1", "p2"),
        admissibility_by_profile={"p1": True, "p2": True},
        compressed_values={"p1": "same", "p2": "same"},
    )
    builder.add_compression_factorization(
        factorization_id="factor",
        profile_class_id="class",
        beta_by_value={"same": True},
    )
    codes = _codes(builder.finalize())
    assert "compression.exactness_violation" not in codes
    assert "compression.factorization_missing" not in codes


def test_cli_coverage_and_init_are_v04(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["coverage"]) == 0
    coverage = json.loads(capsys.readouterr().out)
    assert coverage["summary"]["complete"] is True
    assert coverage["summary"]["counts"]["implemented"] >= 184

    assert main(["init", "--mode", "draft", "--agent-id", "agent-v4"]) == 0
    initialized = json.loads(capsys.readouterr().out)
    assert initialized["schema_version"] == "1.0"
    ledger = EvaluatedLedger.from_dict(initialized)
    assert validate_ledger(ledger).errors == ()
