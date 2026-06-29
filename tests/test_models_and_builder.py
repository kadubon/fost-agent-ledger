from __future__ import annotations

import json

import pytest

from fost_agent_ledger import LedgerBuilder, validate_ledger
from fost_agent_ledger.enums import Admissibility, LedgerStage, RecordType, Status, SupportRole
from fost_agent_ledger.errors import StageFrozenError
from fost_agent_ledger.ledger import EvaluatedLedger
from fost_agent_ledger.model import LedgerRecord
from fost_agent_ledger.serialization import export_json_schema, from_json, from_json_lines, to_json


def test_enum_values_are_stable_lowercase_strings() -> None:
    assert RecordType.CERTIFICATE_TARGET.value == "certificate_target"
    assert LedgerStage.CHECKED_ADMISSIBILITY.value == "checked_admissibility"
    assert SupportRole.ADMISSIBILITY_CHECK.value == "admissibility_check"


def test_builder_validation_and_json_roundtrip() -> None:
    builder = LedgerBuilder(agent_id="agent-1", mode="draft")
    claim = builder.add_claim("Finite support is recorded.")
    builder.add_support("The claim has one support record.", supports=[claim.id])
    ledger = builder.finalize()

    result = validate_ledger(ledger)
    assert result.status == Status.SUPPORTED
    assert result.admissibility == Admissibility.ADMISSIBLE

    loaded = from_json(to_json(ledger))
    assert loaded.records[0].payload == ledger.records[0].payload
    assert loaded.support_graph.edges[0].target_id == claim.id


def test_json_lines_roundtrip() -> None:
    builder = LedgerBuilder(agent_id="agent-1", mode="draft")
    builder.add_claim("A claim")
    ledger = builder.finalize()
    loaded = from_json_lines(ledger.to_json_lines(), agent_id="agent-1", mode="draft")
    assert len(loaded.records) == 1


def test_stage_freeze_prevents_later_rewrite() -> None:
    ledger = EvaluatedLedger(agent_id="agent", mode="draft").freeze_stage("candidate")
    record = LedgerRecord.create(RecordType.CLAIM, LedgerStage.CANDIDATE, {"text": "x"})
    with pytest.raises(StageFrozenError):
        ledger.add_record(record)


def test_schema_exports_major_defs() -> None:
    schema = export_json_schema()
    assert "LedgerRecord" in schema["$defs"]
    assert "ValidationResult" in schema["$defs"]
    assert json.dumps(schema)
