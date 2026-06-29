from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import ProblemSeverity
from .model import JsonDict, JsonModel, Problem


@dataclass(frozen=True)
class EventOrder(JsonModel):
    events: tuple[str, ...] = ("event-0",)
    order_edges: tuple[tuple[str, str], ...] = ()
    current_event: str = "event-0"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventOrder:
        return cls(
            events=tuple(str(item) for item in data.get("events", ("event-0",))),
            order_edges=tuple(
                (str(item[0]), str(item[1]))
                for item in data.get("order_edges", ())
                if isinstance(item, (list, tuple)) and len(item) == 2
            ),
            current_event=str(data.get("current_event", data.get("current_event_id", "event-0"))),
        )

    def position(self, event_id: str) -> int:
        if event_id in self.events:
            return self.events.index(event_id)
        return len(self.events)

    def validate(self) -> tuple[Problem, ...]:
        problems: list[Problem] = []
        event_set = set(self.events)
        if self.current_event not in event_set:
            problems.append(
                Problem(
                    code="event.current_missing",
                    message="current event is not in the finite event set",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(self.current_event,),
                )
            )
        for before, after in self.order_edges:
            if before not in event_set or after not in event_set:
                problems.append(
                    Problem(
                        code="event.edge_missing_endpoint",
                        message="event-order edge cites an unknown event",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(before, after),
                    )
                )
            if before == after:
                problems.append(
                    Problem(
                        code="event.self_cycle",
                        message="event-order edge cannot point to itself",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(before,),
                    )
                )
            if self.position(before) > self.position(after):
                problems.append(
                    Problem(
                        code="event.order_conflict",
                        message="event-order edge conflicts with declared event sequence",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(before, after),
                    )
                )
        return tuple(problems)


@dataclass(frozen=True)
class ProvenanceEdge(JsonModel):
    source_id: str
    source_event: str
    target_id: str
    target_event: str
    version_id: str
    reason: str = ""
    metadata: JsonDict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProvenanceEdge:
        return cls(
            source_id=str(data["source_id"]),
            source_event=str(data.get("source_event", "event-0")),
            target_id=str(data["target_id"]),
            target_event=str(data.get("target_event", "event-0")),
            version_id=str(data.get("version_id", "unknown")),
            reason=str(data.get("reason", "")),
            metadata=dict(data.get("metadata", {})),
        )


def validate_provenance(
    *,
    provenance_edges: tuple[ProvenanceEdge, ...],
    event_order: EventOrder,
    node_ids: set[str],
) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    for edge in provenance_edges:
        if edge.source_id not in node_ids or edge.target_id not in node_ids:
            problems.append(
                Problem(
                    code="provenance.missing_endpoint",
                    message="provenance edge cites an unknown node",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(edge.source_id, edge.target_id),
                )
            )
        if (
            edge.source_event not in event_order.events
            or edge.target_event not in event_order.events
        ):
            problems.append(
                Problem(
                    code="provenance.missing_event",
                    message="provenance edge cites an unknown event",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(edge.source_event, edge.target_event),
                )
            )
        if edge.source_event == edge.target_event and edge.source_id == edge.target_id:
            problems.append(
                Problem(
                    code="provenance.self_reference",
                    message="provenance edge cannot support a node by itself in one event",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(edge.source_id,),
                )
            )
        if event_order.position(edge.source_event) > event_order.position(edge.target_event):
            problems.append(
                Problem(
                    code="provenance.future_dependency",
                    message="provenance edge depends on a later event",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(edge.source_id, edge.target_id),
                )
            )
    return tuple(problems)
