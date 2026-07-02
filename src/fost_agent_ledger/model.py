from __future__ import annotations

import json
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, TypeVar, cast

from .enums import (
    Admissibility,
    LedgerStage,
    ProblemSeverity,
    RecordType,
    Status,
    SupportRole,
    UnavailablePolicy,
)
from .ids import new_id, utc_now

T = TypeVar("T", bound=Enum)


JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
JsonDict = dict[str, JsonValue]
CANONICAL_SCHEMA_VERSION = "2.0"


def enum_value(enum_cls: type[T], value: T | str) -> T:
    if isinstance(value, enum_cls):
        return value
    return enum_cls(value)


def parse_datetime(value: datetime | str | None) -> datetime:
    if value is None:
        return utc_now()
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def to_plain(value: Any) -> JsonValue:
    if isinstance(value, Enum):
        enum_raw = value.value
        if isinstance(enum_raw, (bool, int, float, str)) or enum_raw is None:
            return enum_raw
        return str(enum_raw)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return {field.name: to_plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(key): to_plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_plain(item) for item in value]
    if value is None or isinstance(value, (bool, int, float, str)):
        return cast(JsonValue, value)
    return str(value)


class JsonModel:
    """Mixin for dataclasses that expose stable dictionary and JSON output."""

    json_sort_keys: ClassVar[bool] = True

    def to_dict(self) -> JsonDict:
        value = to_plain(self)
        if not isinstance(value, dict):
            msg = f"{type(self).__name__}.to_dict() did not produce an object"
            raise TypeError(msg)
        return value

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=self.json_sort_keys)


@dataclass(frozen=True)
class Problem(JsonModel):
    code: str
    message: str
    severity: ProblemSeverity = ProblemSeverity.ERROR
    related_record_ids: tuple[str, ...] = ()
    suggested_repair: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Problem:
        return cls(
            code=str(data["code"]),
            message=str(data["message"]),
            severity=ProblemSeverity(data.get("severity", ProblemSeverity.ERROR.value)),
            related_record_ids=tuple(str(item) for item in data.get("related_record_ids", ())),
            suggested_repair=data.get("suggested_repair"),
        )


@dataclass(frozen=True)
class LedgerRecord(JsonModel):
    record_type: RecordType
    stage: LedgerStage
    payload: JsonDict
    id: str = field(default_factory=lambda: new_id("rec"))
    event_id: str = "event-0"
    timestamp: datetime = field(default_factory=utc_now)
    source: str = "unknown"
    support_refs: tuple[str, ...] = ()
    metadata: JsonDict = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        record_type: RecordType | str,
        stage: LedgerStage | str,
        payload: dict[str, Any] | None = None,
        *,
        id: str | None = None,
        event_id: str = "event-0",
        source: str = "unknown",
        support_refs: tuple[str, ...] | list[str] = (),
        metadata: dict[str, Any] | None = None,
    ) -> LedgerRecord:
        return cls(
            id=id or new_id(str(record_type)),
            record_type=RecordType(record_type),
            stage=LedgerStage(stage),
            event_id=event_id,
            source=source,
            payload=to_plain(payload or {}),  # type: ignore[arg-type]
            support_refs=tuple(support_refs),
            metadata=to_plain(metadata or {}),  # type: ignore[arg-type]
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LedgerRecord:
        return cls(
            id=str(data["id"]),
            record_type=RecordType(data["record_type"]),
            stage=LedgerStage(data["stage"]),
            event_id=str(data.get("event_id", "event-0")),
            timestamp=parse_datetime(data.get("timestamp")),
            source=str(data.get("source", "unknown")),
            payload=dict(data.get("payload", {})),
            support_refs=tuple(str(item) for item in data.get("support_refs", ())),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class SupportEdge(JsonModel):
    source_id: str
    target_id: str
    role: SupportRole = SupportRole.DATA
    reason: str = ""
    event_id: str = "event-0"
    witness_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SupportEdge:
        return cls(
            source_id=str(data["source_id"]),
            target_id=str(data["target_id"]),
            role=SupportRole(data.get("role", SupportRole.DATA.value)),
            reason=str(data.get("reason", "")),
            event_id=str(data.get("event_id", "event-0")),
            witness_id=data.get("witness_id"),
        )


@dataclass(frozen=True)
class FrontierItem(JsonModel):
    node_id: str
    role: SupportRole
    necessity: str = "required"
    unavailable_policy: UnavailablePolicy = UnavailablePolicy.BLOCK
    reason: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FrontierItem:
        return cls(
            node_id=str(data["node_id"]),
            role=SupportRole(data.get("role", SupportRole.DATA.value)),
            necessity=str(data.get("necessity", "required")),
            unavailable_policy=UnavailablePolicy(
                data.get("unavailable_policy", UnavailablePolicy.BLOCK.value)
            ),
            reason=str(data.get("reason", "")),
        )


@dataclass(frozen=True)
class SupportClosure(JsonModel):
    root_id: str
    nodes: tuple[str, ...]
    anchors: tuple[str, ...] = ()
    unavailable_leaves: tuple[str, ...] = ()
    problems: tuple[Problem, ...] = ()

    @property
    def ok(self) -> bool:
        return not any(
            problem.severity in {ProblemSeverity.ERROR, ProblemSeverity.BLOCKER}
            for problem in self.problems
        )


@dataclass(frozen=True)
class ValidationResult(JsonModel):
    status: Status
    admissibility: Admissibility
    errors: tuple[Problem, ...] = ()
    warnings: tuple[Problem, ...] = ()
    issues: tuple[LedgerRecord, ...] = ()
    obligations: tuple[LedgerRecord, ...] = ()
    missing_support: tuple[Problem, ...] = ()
    certificate_problems: tuple[Problem, ...] = ()
    environment_problems: tuple[Problem, ...] = ()
    transition_problems: tuple[Problem, ...] = ()
    summary: str = ""
    records_checked: int = 0

    @property
    def ok(self) -> bool:
        return self.admissibility == Admissibility.ADMISSIBLE and not self.errors

    @property
    def open_issues(self) -> tuple[LedgerRecord, ...]:
        return self.issues

    @property
    def open_obligations(self) -> tuple[LedgerRecord, ...]:
        return self.obligations

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ValidationResult:
        return cls(
            status=Status(data["status"]),
            admissibility=Admissibility(data["admissibility"]),
            errors=tuple(Problem.from_dict(item) for item in data.get("errors", ())),
            warnings=tuple(Problem.from_dict(item) for item in data.get("warnings", ())),
            issues=tuple(LedgerRecord.from_dict(item) for item in data.get("issues", ())),
            obligations=tuple(LedgerRecord.from_dict(item) for item in data.get("obligations", ())),
            missing_support=tuple(
                Problem.from_dict(item) for item in data.get("missing_support", ())
            ),
            certificate_problems=tuple(
                Problem.from_dict(item) for item in data.get("certificate_problems", ())
            ),
            environment_problems=tuple(
                Problem.from_dict(item) for item in data.get("environment_problems", ())
            ),
            transition_problems=tuple(
                Problem.from_dict(item) for item in data.get("transition_problems", ())
            ),
            summary=str(data.get("summary", "")),
            records_checked=int(data.get("records_checked", 0)),
        )


@dataclass(frozen=True)
class OperationalCut(JsonModel):
    schema_version: str
    cut_id: str
    created_at: datetime
    agent_id: str
    mode: str
    expression: str | None = None
    output_ref: str | None = None
    event_order: JsonDict = field(
        default_factory=lambda: {"events": ["event-0"], "order_edges": []}
    )
    validation_kernel: str | None = None
    object_kernel: str | None = None
    root_declarations: tuple[str, ...] = ()
    ledger: JsonDict = field(default_factory=dict)
    support_graph: JsonDict = field(default_factory=dict)
    certificate_registry: JsonDict = field(default_factory=dict)
    kernel: JsonDict = field(default_factory=dict)
    environment_envelope: JsonDict = field(default_factory=dict)
    theory_coverage: JsonDict = field(default_factory=dict)
    process_class_registry: JsonDict = field(default_factory=dict)
    presentation_basis: JsonDict = field(default_factory=dict)
    requirement_policy: JsonDict = field(default_factory=dict)
    settledness_licenses: JsonDict = field(default_factory=dict)
    obstruction_profile: JsonDict = field(default_factory=dict)
    compression_witness: JsonDict = field(default_factory=dict)
    self_modification_witness: JsonDict = field(default_factory=dict)
    provenance_edges: tuple[JsonDict, ...] = ()

    @classmethod
    def create(
        cls,
        *,
        agent_id: str,
        mode: str,
        expression: str | None = None,
        output_ref: str | None = None,
    ) -> OperationalCut:
        event_order: JsonDict = {
            "current_event": "event-0",
            "events": ["event-0"],
            "order_edges": [],
        }
        support_graph: JsonDict = {}
        return cls(
            schema_version=CANONICAL_SCHEMA_VERSION,
            cut_id=new_id("cut"),
            created_at=utc_now(),
            agent_id=agent_id,
            mode=mode,
            expression=expression,
            output_ref=output_ref,
            event_order=event_order,
            ledger={
                "schema_version": CANONICAL_SCHEMA_VERSION,
                "agent_id": agent_id,
                "mode": mode,
                "records": [],
                "support_graph": support_graph,
                "event_order": event_order,
                "provenance_edges": [],
                "stage_builds": [],
                "frozen_stages": [],
                "metadata": {},
            },
            support_graph=support_graph,
        )

    @classmethod
    def from_ledger(cls, ledger: Any, *, expression: str | None = None) -> OperationalCut:
        ledger_dict = ledger.to_dict()
        return cls(
            schema_version=str(ledger_dict.get("schema_version", CANONICAL_SCHEMA_VERSION)),
            cut_id=str(ledger_dict.get("metadata", {}).get("cut_id", new_id("cut"))),
            created_at=utc_now(),
            agent_id=str(ledger_dict["agent_id"]),
            mode=str(ledger_dict["mode"]),
            expression=expression,
            ledger=ledger_dict,
            support_graph=dict(ledger_dict.get("support_graph", {})),
            event_order=dict(ledger_dict.get("event_order", {})),
            provenance_edges=tuple(
                item for item in ledger_dict.get("provenance_edges", ()) if isinstance(item, dict)
            ),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OperationalCut:
        schema_version = str(data.get("schema_version", CANONICAL_SCHEMA_VERSION))
        ledger = dict(data.get("ledger", {}))
        if schema_version != CANONICAL_SCHEMA_VERSION:
            schema_version = CANONICAL_SCHEMA_VERSION
        if ledger and ledger.get("schema_version") != CANONICAL_SCHEMA_VERSION:
            metadata = dict(ledger.get("metadata", {}))
            metadata.setdefault(
                "migrated_from_schema_version",
                str(ledger.get("schema_version", data.get("schema_version", "0.1"))),
            )
            ledger["schema_version"] = CANONICAL_SCHEMA_VERSION
            ledger["metadata"] = metadata
        return cls(
            schema_version=schema_version,
            cut_id=str(data["cut_id"]),
            created_at=parse_datetime(data.get("created_at")),
            agent_id=str(data["agent_id"]),
            mode=str(data["mode"]),
            expression=data.get("expression"),
            output_ref=data.get("output_ref"),
            event_order=dict(data.get("event_order", {"events": ["event-0"], "order_edges": []})),
            validation_kernel=data.get("validation_kernel"),
            object_kernel=data.get("object_kernel"),
            root_declarations=tuple(str(item) for item in data.get("root_declarations", ())),
            ledger=ledger,
            support_graph=dict(data.get("support_graph", {})),
            certificate_registry=dict(data.get("certificate_registry", {})),
            kernel=dict(data.get("kernel", {})),
            environment_envelope=dict(data.get("environment_envelope", {})),
            theory_coverage=dict(data.get("theory_coverage", {})),
            process_class_registry=dict(data.get("process_class_registry", {})),
            presentation_basis=dict(data.get("presentation_basis", {})),
            requirement_policy=dict(data.get("requirement_policy", {})),
            settledness_licenses=dict(data.get("settledness_licenses", {})),
            obstruction_profile=dict(data.get("obstruction_profile", {})),
            compression_witness=dict(data.get("compression_witness", {})),
            self_modification_witness=dict(data.get("self_modification_witness", {})),
            provenance_edges=tuple(
                item for item in data.get("provenance_edges", ()) if isinstance(item, dict)
            ),
        )
