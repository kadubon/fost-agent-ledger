from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .admissibility import validate_ledger
from .enums import Admissibility, ProblemSeverity, RecordType
from .ledger import EvaluatedLedger
from .model import JsonDict, JsonModel, Problem, to_plain
from .modes import ModeContract


@dataclass(frozen=True)
class TransitionWitness(JsonModel):
    coordinate: str
    witness_record_id: str
    reason: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransitionWitness:
        return cls(
            coordinate=str(data["coordinate"]),
            witness_record_id=str(data["witness_record_id"]),
            reason=str(data.get("reason", "")),
        )


@dataclass(frozen=True)
class LedgerTransition(JsonModel):
    previous_cut_id: str
    next_cut_id: str
    changed_support_coordinates: tuple[str, ...] = ()
    changed_kernel_coordinates: tuple[str, ...] = ()
    changed_certificate_states: tuple[str, ...] = ()
    changed_obligations: tuple[str, ...] = ()
    changed_environment_tokens: tuple[str, ...] = ()
    changed_mode_or_scope: tuple[str, ...] = ()
    changed_provenance_coordinates: tuple[str, ...] = ()
    changed_event_order_coordinates: tuple[str, ...] = ()
    changed_status_admissibility_coordinates: tuple[str, ...] = ()
    witnesses: tuple[TransitionWitness, ...] = ()
    metadata: JsonDict = field(default_factory=dict)

    @property
    def changed_coordinates(self) -> tuple[str, ...]:
        return (
            self.changed_support_coordinates
            + self.changed_kernel_coordinates
            + self.changed_certificate_states
            + self.changed_obligations
            + self.changed_environment_tokens
            + self.changed_mode_or_scope
            + self.changed_provenance_coordinates
            + self.changed_event_order_coordinates
            + self.changed_status_admissibility_coordinates
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LedgerTransition:
        return cls(
            previous_cut_id=str(data["previous_cut_id"]),
            next_cut_id=str(data["next_cut_id"]),
            changed_support_coordinates=tuple(
                str(item) for item in data.get("changed_support_coordinates", ())
            ),
            changed_kernel_coordinates=tuple(
                str(item) for item in data.get("changed_kernel_coordinates", ())
            ),
            changed_certificate_states=tuple(
                str(item) for item in data.get("changed_certificate_states", ())
            ),
            changed_obligations=tuple(str(item) for item in data.get("changed_obligations", ())),
            changed_environment_tokens=tuple(
                str(item) for item in data.get("changed_environment_tokens", ())
            ),
            changed_mode_or_scope=tuple(
                str(item) for item in data.get("changed_mode_or_scope", ())
            ),
            changed_provenance_coordinates=tuple(
                str(item) for item in data.get("changed_provenance_coordinates", ())
            ),
            changed_event_order_coordinates=tuple(
                str(item) for item in data.get("changed_event_order_coordinates", ())
            ),
            changed_status_admissibility_coordinates=tuple(
                str(item) for item in data.get("changed_status_admissibility_coordinates", ())
            ),
            witnesses=tuple(
                TransitionWitness.from_dict(item)
                for item in data.get("witnesses", ())
                if isinstance(item, dict)
            ),
            metadata=dict(data.get("metadata", {})),
        )


def diff_ledgers(before: EvaluatedLedger, after: EvaluatedLedger) -> LedgerTransition:
    changed_records = _changed_record_ids(before, after)
    record_types = _record_types(before, after)
    support_records = {
        RecordType.CLAIM,
        RecordType.SUPPORT,
        RecordType.EVIDENCE,
        RecordType.PROCESS_CLASS,
        RecordType.DISTINCTION_BASIS,
        RecordType.FINITE_PRESENTATION,
        RecordType.PRESENTATION_MAP,
        RecordType.FINITE_EXPRESSION,
        RecordType.REQUIREMENT,
        RecordType.REQUIREMENT_POLICY,
        RecordType.REQUIREMENT_REASON,
        RecordType.REQUIREMENT_TRANSFER,
        RecordType.ISSUE,
        RecordType.RESIDUE,
        RecordType.OBSTRUCTION,
        RecordType.SETTLEDNESS_DECLARATION,
        RecordType.SETTLEDNESS_LICENSE,
        RecordType.OBSTRUCTION_PROFILE,
        RecordType.UNAVAILABLE_LEAF,
        RecordType.ACCEPTANCE,
        RecordType.ABSTENTION,
        RecordType.FAILURE,
        RecordType.MODE_FILTERED_FAILURE,
        RecordType.GATE_REQUIREMENT,
        RecordType.GATE_PASS,
        RecordType.IMPACT_RECORD,
        RecordType.CRITIC_COVERAGE,
        RecordType.SCOPE_EXCLUSION,
        RecordType.MODE_CLOSURE,
        RecordType.COMPRESSION_USE,
        RecordType.COMPRESSION_PROFILE_CLASS,
        RecordType.COMPRESSION_FACTORIZATION,
        RecordType.CONSISTENCY_PROFILE,
        RecordType.VALIDATOR_TIMEOUT,
        RecordType.RECORD_PRESERVING_REFINEMENT,
        RecordType.SELF_MODIFICATION_WITNESS,
        RecordType.THEORY_ITEM_COVERAGE,
    }
    certificate_records = {
        RecordType.CERTIFICATE_STATE,
        RecordType.CERTIFICATE_USE,
        RecordType.NULL_CERTIFICATE,
        RecordType.CERTIFICATE_COVER,
        RecordType.RESPECT_CERTIFICATE,
    }
    return LedgerTransition(
        previous_cut_id=str(before.metadata.get("cut_id", "before")),
        next_cut_id=str(after.metadata.get("cut_id", "after")),
        changed_support_coordinates=tuple(
            sorted(
                record_id
                for record_id in changed_records
                if record_types.get(record_id) in support_records
            )
        )
        + _changed_object_coordinate(
            before.support_graph.to_dict(),
            after.support_graph.to_dict(),
            "support_graph",
        ),
        changed_certificate_states=tuple(
            sorted(
                record_id
                for record_id in changed_records
                if record_types.get(record_id) in certificate_records
            )
        ),
        changed_obligations=tuple(
            sorted(
                record_id
                for record_id in changed_records
                if record_types.get(record_id)
                in {
                    RecordType.OBLIGATION,
                    RecordType.OBLIGATION_LIFECYCLE,
                    RecordType.OBLIGATION_DISCHARGE,
                }
            )
        ),
        changed_environment_tokens=tuple(
            sorted(
                record_id
                for record_id in changed_records
                if record_types.get(record_id) == RecordType.ENVIRONMENT_TOKEN
            )
        ),
        changed_mode_or_scope=_changed_mode_or_scope(before, after),
        changed_provenance_coordinates=_changed_object_coordinate(
            [edge.to_dict() for edge in before.provenance_edges],
            [edge.to_dict() for edge in after.provenance_edges],
            "provenance_edges",
        ),
        changed_event_order_coordinates=_changed_object_coordinate(
            before.event_order.to_dict(),
            after.event_order.to_dict(),
            "event_order",
        ),
        changed_status_admissibility_coordinates=tuple(
            sorted(
                record_id
                for record_id in changed_records
                if record_types.get(record_id)
                in {RecordType.STATUS, RecordType.ADMISSIBILITY, RecordType.VALIDATION_RESULT}
            )
        ),
    )


def validate_transition(
    before: EvaluatedLedger,
    after: EvaluatedLedger,
    transition: LedgerTransition | None = None,
    *,
    mode: ModeContract | str | None = None,
) -> tuple[Problem, ...]:
    transition = transition or diff_ledgers(before, after)
    problems: list[Problem] = []
    witnesses = {witness.coordinate for witness in transition.witnesses}
    after_ids = {record.id for record in after.records}
    for coordinate in transition.changed_coordinates:
        if coordinate not in witnesses:
            problems.append(
                Problem(
                    code="transition.missing_witness",
                    message=f"changed coordinate {coordinate!r} has no transition witness",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(coordinate,),
                )
            )
    for witness in transition.witnesses:
        if witness.witness_record_id not in after_ids and witness.witness_record_id != "external":
            problems.append(
                Problem(
                    code="transition.missing_witness_record",
                    message="transition witness points to no finite next-ledger record",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(witness.coordinate, witness.witness_record_id),
                )
            )

    before_result = validate_ledger(before, mode=mode)
    after_result = validate_ledger(after, mode=mode)
    gained = (
        before_result.admissibility != Admissibility.ADMISSIBLE
        and after_result.admissibility == Admissibility.ADMISSIBLE
    )
    witnessed_pre_admissibility_change = bool(
        witnesses
        & set(
            transition.changed_support_coordinates
            + transition.changed_kernel_coordinates
            + transition.changed_certificate_states
            + transition.changed_obligations
            + transition.changed_environment_tokens
            + transition.changed_mode_or_scope
            + transition.changed_provenance_coordinates
            + transition.changed_event_order_coordinates
        )
    )
    if gained and not witnessed_pre_admissibility_change:
        problems.append(
            Problem(
                code="transition.untraced_admissibility_gain",
                message="admissibility improved without witnessed pre-admissibility support change",
                severity=ProblemSeverity.ERROR,
                suggested_repair=(
                    "Record changed pre-admissibility support coordinates or "
                    "validator/kernel coordinates with witnesses."
                ),
            )
        )
    return tuple(problems)


def _changed_record_ids(before: EvaluatedLedger, after: EvaluatedLedger) -> tuple[str, ...]:
    before_records = {record.id: record.to_dict() for record in before.records}
    after_records = {record.id: record.to_dict() for record in after.records}
    changed = []
    for record_id in sorted(set(before_records) | set(after_records)):
        if _stable_json(before_records.get(record_id)) != _stable_json(
            after_records.get(record_id)
        ):
            changed.append(record_id)
    return tuple(changed)


def _record_types(before: EvaluatedLedger, after: EvaluatedLedger) -> dict[str, RecordType]:
    types: dict[str, RecordType] = {}
    for record in before.records + after.records:
        types[record.id] = record.record_type
    return types


def _changed_mode_or_scope(before: EvaluatedLedger, after: EvaluatedLedger) -> tuple[str, ...]:
    changed = []
    if before.mode != after.mode:
        changed.append("mode")
    before_scope = before.metadata.get("scope")
    after_scope = after.metadata.get("scope")
    if _stable_json(before_scope) != _stable_json(after_scope):
        changed.append("scope")
    return tuple(changed)


def _changed_object_coordinate(before: Any, after: Any, coordinate: str) -> tuple[str, ...]:
    if _stable_json(before) == _stable_json(after):
        return ()
    return (coordinate,)


def _stable_json(value: Any) -> str:
    return json.dumps(to_plain(value), sort_keys=True, separators=(",", ":"))
