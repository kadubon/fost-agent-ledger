from __future__ import annotations

import json
from pathlib import Path

import pytest

from fost_agent_ledger import LedgerBuilder, UnknownModeError, validate_ledger
from fost_agent_ledger.certificates import scope_covers
from fost_agent_ledger.cli import main
from fost_agent_ledger.enums import AnchorKind, LedgerStage, RecordType
from fost_agent_ledger.ledger import EvaluatedLedger
from fost_agent_ledger.model import LedgerRecord
from fost_agent_ledger.serialization import export_json_schema


def _codes(ledger: EvaluatedLedger, *, require_finality: bool = True) -> set[str]:
    return {
        problem.code
        for problem in validate_ledger(ledger, require_finality=require_finality).errors
    }


def test_finalize_checked_builds_strict_finality_path() -> None:
    builder = LedgerBuilder(agent_id="agent", mode="draft")
    claim = builder.add_claim("A finite claim")
    builder.add_support("Finite support", supports=[claim.id])

    ledger = builder.finalize_checked()
    result = validate_ledger(ledger, require_finality=True)

    assert ledger.schema_version == "2.0"
    assert result.errors == ()
    assert result.ok
    assert ledger.find(RecordType.STATUS_BODY)
    assert ledger.find(RecordType.CHECKED_STATUS)
    assert ledger.find(RecordType.PRE_ADMISSIBILITY_SUPPORT_VECTOR)
    assert ledger.find(RecordType.ADMISSIBILITY_BODY)
    assert ledger.find(RecordType.CHECKED_ADMISSIBILITY)


def test_require_finality_reports_missing_typed_records() -> None:
    builder = LedgerBuilder(agent_id="agent", mode="draft")
    claim = builder.add_claim("A finite claim")
    builder.add_support("Finite support", supports=[claim.id])

    codes = _codes(builder.finalize())

    assert "finality.missing_status_body" in codes
    assert "finality.missing_checked_status" in codes
    assert "finality.missing_pre_vector" in codes
    assert "finality.missing_admissibility_body" in codes
    assert "finality.missing_checked_admissibility" in codes
    assert "kernel.missing_context" in codes


def test_strict_anchor_declaration_and_unavailable_evidence() -> None:
    builder = LedgerBuilder(agent_id="agent", mode="draft")
    claim = builder.add_claim("A finite claim")
    support = builder.add_support("Finite support", supports=[claim.id])
    status_body = builder.add_status_body(
        target_id=claim.id,
        support_refs=("missing-leaf",),
        checker_version_id="checker",
        rule_version_id="rules",
    )
    builder.add_checked_status(
        body_record_id=status_body.id,
        checker_version_id="checker",
        rule_version_id="rules",
    )
    ledger = builder.ledger.mark_unavailable("missing-leaf", "not available")

    codes = _codes(ledger)

    assert "anchor.undeclared" in codes
    assert "support.unavailable_evidence" in codes
    assert support.id in ledger.support_graph.anchors


def test_declared_anchor_can_pass_strict_anchor_check() -> None:
    builder = LedgerBuilder(agent_id="agent", mode="draft")
    claim = builder.add_claim("A finite claim")
    support = builder.add_support("Finite support", supports=[claim.id])
    builder.add_anchor_declaration(
        anchor_id=support.id,
        anchor_kind=AnchorKind.DECLARED_SUPPORT,
        reason="explicit anchor",
    )

    assert "anchor.undeclared" not in _codes(builder.finalize_checked())


def test_certificate_scope_is_fail_closed() -> None:
    assert not scope_covers({}, {"mode": "agent_action"})
    assert not scope_covers({"mode": ["draft"]}, {"mode": "agent_action"})
    assert not scope_covers({"env": {"region": "us"}}, {"env": {"region": "us", "tier": "prod"}})
    assert scope_covers({"mode": "*"}, {"mode": "agent_action"})
    assert scope_covers({"mode": ["draft", "agent_action"]}, {"mode": ["draft"]})


def test_unknown_mode_is_rejected_unless_fallback_is_explicit(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ledger = EvaluatedLedger(agent_id="agent", mode="custom_mode")

    with pytest.raises(UnknownModeError):
        validate_ledger(ledger)

    path = tmp_path / "ledger.json"
    path.write_text(ledger.to_json(), encoding="utf-8")
    assert main(["validate", str(path)]) == 2
    assert json.loads(capsys.readouterr().out)["code"] == "mode.unknown"

    assert main(["validate", str(path), "--allow-unknown-mode-as-draft"]) == 0
    assert json.loads(capsys.readouterr().out)["admissibility"] in {
        "admissible",
        "unknown",
        "inadmissible",
    }


def test_strict_finality_rejects_output_leakage_and_missing_versions() -> None:
    status_body = LedgerRecord.create(
        RecordType.STATUS_BODY,
        LedgerStage.CHECKED_STATUS,
        {"body_id": "body", "target_id": "claim", "reads_final_output": True},
        id="body",
    )
    checked_status = LedgerRecord.create(
        RecordType.CHECKED_STATUS,
        LedgerStage.CHECKED_STATUS,
        {
            "status_id": "status",
            "body_record_id": "body",
            "status": "supported",
            "checker_version_id": "",
            "rule_version_id": "",
        },
        id="status",
    )
    ledger = EvaluatedLedger(agent_id="agent", mode="draft").add_records(
        (status_body, checked_status)
    )

    codes = _codes(ledger)

    assert "finality.output_leakage" in codes
    assert "status.missing_checker_or_rule_version" in codes


def test_v20_schema_exposes_strict_payloads() -> None:
    schema = export_json_schema()
    defs = schema["$defs"]

    assert schema["$id"].endswith("fost-agent-ledger-2.0.schema.json")
    for name in {
        "AnchorDeclarationPayload",
        "AdequacyRecordPayload",
        "StatusBodyPayload",
        "CheckedStatusPayload",
        "PreAdmissibilitySupportVectorPayload",
        "AdmissibilityBodyPayload",
        "CheckedAdmissibilityPayload",
    }:
        assert name in defs
