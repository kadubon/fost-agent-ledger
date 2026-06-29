from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from typing import Any

from .enums import STAGE_ORDER, LedgerStage, ProblemSeverity, RecordType
from .errors import MissingRecordError, SerializationError, StageFrozenError
from .model import JsonDict, JsonModel, LedgerRecord, Problem, SupportEdge, to_plain
from .payloads import parse_payload
from .provenance import EventOrder, ProvenanceEdge
from .stages import StageBuildRecord, validate_stage_builds
from .support import SupportGraph

SCHEMA_VERSION = "1.0"


def stage_index(stage: LedgerStage | str) -> int:
    return STAGE_ORDER.index(LedgerStage(stage))


@dataclass(frozen=True)
class EvaluatedLedger(JsonModel):
    """Stage-tagged finite ledger.

    The object stores records in append-only form. Freezing a stage prevents later writes to that
    stage, which mirrors FOST's phase-normal construction: later stages may append later records,
    but they do not silently rewrite earlier outputs.
    """

    agent_id: str
    mode: str
    schema_version: str = SCHEMA_VERSION
    records: tuple[LedgerRecord, ...] = ()
    support_graph: SupportGraph = field(default_factory=SupportGraph)
    event_order: EventOrder = field(default_factory=EventOrder)
    provenance_edges: tuple[ProvenanceEdge, ...] = ()
    stage_builds: tuple[StageBuildRecord, ...] = ()
    frozen_stages: tuple[LedgerStage, ...] = ()
    metadata: JsonDict = field(default_factory=dict)

    def add_record(self, record: LedgerRecord) -> EvaluatedLedger:
        if record.stage in self.frozen_stages:
            raise StageFrozenError(f"stage {record.stage.value} is frozen")
        graph = self.support_graph.add_node(record)
        return replace(self, records=(*self.records, record), support_graph=graph)

    def add_records(self, records: Iterable[LedgerRecord]) -> EvaluatedLedger:
        ledger = self
        for record in records:
            ledger = ledger.add_record(record)
        return ledger

    def add_support_edge(self, edge: SupportEdge) -> EvaluatedLedger:
        return replace(self, support_graph=self.support_graph.add_edge(edge))

    def add_provenance_edge(self, edge: ProvenanceEdge) -> EvaluatedLedger:
        return replace(self, provenance_edges=(*self.provenance_edges, edge))

    def add_stage_build(self, build: StageBuildRecord) -> EvaluatedLedger:
        return replace(self, stage_builds=(*self.stage_builds, build))

    def mark_anchor(self, record_id: str) -> EvaluatedLedger:
        return replace(self, support_graph=self.support_graph.mark_anchor(record_id))

    def mark_checked(self, record_id: str) -> EvaluatedLedger:
        return replace(self, support_graph=self.support_graph.mark_checked(record_id))

    def mark_unavailable(self, record_id: str, reason: str) -> EvaluatedLedger:
        return replace(self, support_graph=self.support_graph.mark_unavailable(record_id, reason))

    def freeze_stage(self, stage: LedgerStage | str) -> EvaluatedLedger:
        ledger_stage = LedgerStage(stage)
        if ledger_stage in self.frozen_stages:
            return self
        return replace(self, frozen_stages=(*self.frozen_stages, ledger_stage))

    def freeze_through(self, stage: LedgerStage | str) -> EvaluatedLedger:
        target = stage_index(stage)
        ledger = self
        for item in STAGE_ORDER[: target + 1]:
            ledger = ledger.freeze_stage(item)
        return ledger

    def get(self, record_id: str) -> LedgerRecord:
        for record in self.records:
            if record.id == record_id:
                return record
        raise MissingRecordError(record_id)

    def find(self, record_type: RecordType | str | None = None) -> tuple[LedgerRecord, ...]:
        if record_type is None:
            return self.records
        wanted = RecordType(record_type)
        return tuple(record for record in self.records if record.record_type == wanted)

    def by_stage(self, stage: LedgerStage | str) -> tuple[LedgerRecord, ...]:
        wanted = LedgerStage(stage)
        return tuple(record for record in self.records if record.stage == wanted)

    def latest(self, record_type: RecordType | str) -> LedgerRecord | None:
        wanted = RecordType(record_type)
        for record in reversed(self.records):
            if record.record_type == wanted:
                return record
        return None

    def validate_payloads(self) -> tuple[Problem, ...]:
        problems: list[Problem] = []
        for record in self.records:
            try:
                parse_payload(record.record_type, record.payload)
            except (TypeError, ValueError, KeyError) as exc:
                problems.append(
                    Problem(
                        code="payload.invalid",
                        message=(
                            f"{record.record_type.value} payload does not match "
                            f"the v1.0 typed schema: {exc}"
                        ),
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(record.id,),
                    )
                )
                continue
            if (
                record.record_type == RecordType.UNAVAILABLE_LEAF
                and record.payload.get("evidence", False) is True
            ):
                problems.append(
                    Problem(
                        code="unavailable.evidence_misuse",
                        message="unavailable leaf cannot serve as evidence",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(record.id,),
                    )
                )
        return tuple(problems)

    def validate_stage_builds(self) -> tuple[Problem, ...]:
        return validate_stage_builds(
            stage_builds=self.stage_builds,
            record_stages={record.id: record.stage for record in self.records},
        )

    def to_dict(self) -> JsonDict:
        return {
            "schema_version": self.schema_version,
            "agent_id": self.agent_id,
            "mode": self.mode,
            "records": [record.to_dict() for record in self.records],
            "support_graph": self.support_graph.to_dict(),
            "event_order": self.event_order.to_dict(),
            "provenance_edges": [edge.to_dict() for edge in self.provenance_edges],
            "stage_builds": [build.to_dict() for build in self.stage_builds],
            "frozen_stages": [stage.value for stage in self.frozen_stages],
            "metadata": to_plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvaluatedLedger:
        try:
            migrated = _migrate_legacy_ledger_dict(data)
            return cls(
                schema_version=str(migrated.get("schema_version", SCHEMA_VERSION)),
                agent_id=str(migrated["agent_id"]),
                mode=str(migrated["mode"]),
                records=tuple(LedgerRecord.from_dict(item) for item in migrated.get("records", ())),
                support_graph=SupportGraph.from_dict(migrated.get("support_graph", {})),
                event_order=EventOrder.from_dict(migrated.get("event_order", {})),
                provenance_edges=tuple(
                    ProvenanceEdge.from_dict(item)
                    for item in migrated.get("provenance_edges", ())
                    if isinstance(item, dict)
                ),
                stage_builds=tuple(
                    StageBuildRecord.from_dict(item)
                    for item in migrated.get("stage_builds", ())
                    if isinstance(item, dict)
                ),
                frozen_stages=tuple(
                    LedgerStage(item) for item in migrated.get("frozen_stages", ())
                ),
                metadata=dict(migrated.get("metadata", {})),
            )
        except KeyError as exc:
            raise SerializationError(f"ledger is missing required key {exc.args[0]!r}") from exc

    @classmethod
    def from_json(cls, text: str) -> EvaluatedLedger:
        loaded = json.loads(text)
        if not isinstance(loaded, dict):
            raise SerializationError("ledger JSON must be an object")
        return cls.from_dict(loaded)

    def to_json_lines(self) -> str:
        lines = [json.dumps(record.to_dict(), sort_keys=True) for record in self.records]
        return "\n".join(lines)

    @classmethod
    def from_json_lines(
        cls,
        text: str,
        *,
        agent_id: str = "unknown",
        mode: str = "draft",
    ) -> EvaluatedLedger:
        records = []
        for line in text.splitlines():
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise SerializationError("JSON Lines entries must be objects")
                records.append(LedgerRecord.from_dict(value))
        ledger = cls(agent_id=agent_id, mode=mode)
        return ledger.add_records(records)


def _migrate_legacy_ledger_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Return a v1.0-shaped ledger dictionary.

    v0.1/v0.2/v0.3/v0.4 ledgers may lack current finite validation coordinates and
    record types. The migration is structural only; it does not invent validation evidence.
    """

    migrated = dict(data)
    if migrated.get("schema_version") == SCHEMA_VERSION:
        return migrated
    migrated["schema_version"] = SCHEMA_VERSION
    migrated.setdefault("event_order", {"events": ["event-0"], "order_edges": []})
    migrated.setdefault("provenance_edges", [])
    migrated.setdefault("stage_builds", [])
    metadata = dict(migrated.get("metadata", {}))
    metadata.setdefault("migrated_from_schema_version", str(data.get("schema_version", "0.1")))
    migrated["metadata"] = metadata
    return migrated
