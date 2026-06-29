from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from .enums import ProblemSeverity, RecordType, SupportRole, UnavailablePolicy
from .model import (
    FrontierItem,
    JsonDict,
    JsonModel,
    LedgerRecord,
    Problem,
    SupportClosure,
    SupportEdge,
)
from .provenance import EventOrder
from .stages import ValidationCoordinate


@dataclass(frozen=True)
class SupportGraph(JsonModel):
    """Finite directed support graph.

    Edges point from supporting records to supported records. Unavailable leaves terminate
    structural closure but never count as evidence.
    """

    nodes: dict[str, LedgerRecord] = field(default_factory=dict)
    edges: tuple[SupportEdge, ...] = ()
    anchors: tuple[str, ...] = ()
    unavailable: dict[str, str] = field(default_factory=dict)
    checked_nodes: tuple[str, ...] = ()
    frontier_items: dict[str, tuple[FrontierItem, ...]] = field(default_factory=dict)
    validation_coordinates: dict[str, ValidationCoordinate] = field(default_factory=dict)
    anchor_roles: dict[str, tuple[SupportRole, ...]] = field(default_factory=dict)
    allow_cycles: bool = False

    def add_node(self, record: LedgerRecord) -> SupportGraph:
        nodes = dict(self.nodes)
        nodes[record.id] = record
        coordinates = dict(self.validation_coordinates)
        coordinates.setdefault(
            record.id,
            ValidationCoordinate.default_for_record(
                event_id=record.event_id,
                stage=record.stage,
                target_id=str(record.metadata.get("target_id", "null")),
            ),
        )
        return replace(self, nodes=nodes, validation_coordinates=coordinates)

    def add_edge(self, edge: SupportEdge) -> SupportGraph:
        return replace(self, edges=(*self.edges, edge))

    def add_frontier_item(self, target_id: str, item: FrontierItem) -> SupportGraph:
        items = dict(self.frontier_items)
        items[target_id] = (*items.get(target_id, ()), item)
        return replace(self, frontier_items=items)

    def add_validation_coordinate(
        self, record_id: str, coordinate: ValidationCoordinate
    ) -> SupportGraph:
        coordinates = dict(self.validation_coordinates)
        coordinates[record_id] = coordinate
        return replace(self, validation_coordinates=coordinates)

    def mark_anchor(
        self, record_id: str, roles: tuple[SupportRole, ...] | None = None
    ) -> SupportGraph:
        anchor_roles = dict(self.anchor_roles)
        if roles is not None:
            anchor_roles[record_id] = roles
        if record_id in self.anchors:
            return replace(self, anchor_roles=anchor_roles)
        return replace(self, anchors=(*self.anchors, record_id), anchor_roles=anchor_roles)

    def mark_checked(self, record_id: str) -> SupportGraph:
        if record_id in self.checked_nodes:
            return self
        return replace(self, checked_nodes=(*self.checked_nodes, record_id))

    def mark_unavailable(self, record_id: str, reason: str) -> SupportGraph:
        unavailable = dict(self.unavailable)
        unavailable[record_id] = reason
        return replace(self, unavailable=unavailable)

    def incoming(self, target_id: str, role: SupportRole | None = None) -> tuple[SupportEdge, ...]:
        return tuple(
            edge
            for edge in self.edges
            if edge.target_id == target_id and (role is None or edge.role == role)
        )

    def outgoing(self, source_id: str) -> tuple[SupportEdge, ...]:
        return tuple(edge for edge in self.edges if edge.source_id == source_id)

    def detect_missing_references(self) -> tuple[Problem, ...]:
        problems: list[Problem] = []
        for edge in self.edges:
            related = (edge.source_id, edge.target_id)
            if edge.source_id not in self.nodes and edge.source_id not in self.unavailable:
                problems.append(
                    Problem(
                        code="support.missing_source",
                        message=f"support edge source {edge.source_id!r} is not a record",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=related,
                    )
                )
            if edge.target_id not in self.nodes:
                problems.append(
                    Problem(
                        code="support.missing_target",
                        message=f"support edge target {edge.target_id!r} is not a record",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=related,
                    )
                )
        for target, items in self.frontier_items.items():
            if target not in self.nodes:
                problems.append(
                    Problem(
                        code="support.frontier_missing_target",
                        message=f"frontier target {target!r} is not a record",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(target,),
                    )
                )
            for item in items:
                if item.node_id not in self.nodes and item.node_id not in self.unavailable:
                    problems.append(
                        Problem(
                            code="support.frontier_missing_node",
                            message=f"frontier item {item.node_id!r} is not a record",
                            severity=ProblemSeverity.ERROR,
                            related_record_ids=(target, item.node_id),
                        )
                    )
        return tuple(problems)

    def detect_cycles(self) -> tuple[Problem, ...]:
        if self.allow_cycles:
            return ()

        visiting: set[str] = set()
        visited: set[str] = set()
        problems: list[Problem] = []

        def visit(node_id: str, path: tuple[str, ...]) -> None:
            if node_id in visiting:
                cycle_start = path.index(node_id) if node_id in path else 0
                cycle = (*path[cycle_start:], node_id)
                problems.append(
                    Problem(
                        code="support.cycle",
                        message="support graph contains a cycle",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=cycle,
                        suggested_repair=(
                            "Break the same-phase support cycle or mark a permitted "
                            "policy explicitly."
                        ),
                    )
                )
                return
            if node_id in visited:
                return
            visiting.add(node_id)
            for edge in self.outgoing(node_id):
                visit(edge.target_id, (*path, edge.target_id))
            visiting.remove(node_id)
            visited.add(node_id)

        for node_id in self.nodes:
            visit(node_id, (node_id,))
        return tuple(problems)

    def detect_order_violations(self, event_order: EventOrder | None = None) -> tuple[Problem, ...]:
        order = event_order or EventOrder()
        problems: list[Problem] = []
        for edge in self.edges:
            source_record = self.nodes.get(edge.source_id)
            if (
                source_record is not None
                and source_record.record_type == RecordType.CERTIFICATE_STATE
            ):
                continue
            source_coordinate = self.validation_coordinates.get(edge.source_id)
            target_coordinate = self.validation_coordinates.get(edge.target_id)
            if source_coordinate is None or target_coordinate is None:
                continue
            source_key = source_coordinate.key(order.position(source_coordinate.event_id))
            target_key = target_coordinate.key(order.position(target_coordinate.event_id))
            if edge.source_id not in self.anchors and source_key >= target_key:
                problems.append(
                    Problem(
                        code="support.order_violation",
                        message="support edge does not descend by event/stage/phase/target",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(edge.source_id, edge.target_id),
                    )
                )
            same_target_same_phase = (
                source_coordinate.event_id == target_coordinate.event_id
                and source_coordinate.stage == target_coordinate.stage
                and source_coordinate.phase == target_coordinate.phase
                and source_coordinate.target_id == target_coordinate.target_id
                and source_coordinate.target_id != "null"
            )
            if same_target_same_phase:
                problems.append(
                    Problem(
                        code="support.same_target_same_phase",
                        message="same-event same-phase same-target support is not valid",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(edge.source_id, edge.target_id),
                    )
                )
        return tuple(problems)

    def closure(self, record_id: str) -> SupportClosure:
        problems: list[Problem] = list(self.detect_missing_references())
        visited: set[str] = set()
        anchors: set[str] = set()
        unavailable: set[str] = set()
        stack: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in self.unavailable:
                unavailable.add(node_id)
                return
            if node_id in stack and not self.allow_cycles:
                problems.append(
                    Problem(
                        code="support.cycle",
                        message=f"support closure for {record_id!r} contains a cycle",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(record_id, node_id),
                    )
                )
                return
            if node_id in visited:
                return
            if node_id not in self.nodes:
                problems.append(
                    Problem(
                        code="support.missing_node",
                        message=f"support node {node_id!r} is missing",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(record_id, node_id),
                    )
                )
                return

            visited.add(node_id)
            if node_id in self.anchors:
                anchors.add(node_id)
                return

            stack.add(node_id)
            frontier = self.frontier_items.get(node_id, ())
            for item in frontier:
                self._check_frontier_item(node_id, item, problems, unavailable)
                if item.node_id not in self.unavailable:
                    visit(item.node_id)

            for edge in self.incoming(node_id):
                if edge.witness_id is None:
                    problems.append(
                        Problem(
                            code="support.missing_witness",
                            message="support edge has no finite witness",
                            severity=ProblemSeverity.ERROR,
                            related_record_ids=(edge.source_id, edge.target_id),
                            suggested_repair="Add a support witness record for the edge.",
                        )
                    )
                visit(edge.source_id)

            if not frontier and not self.incoming(node_id) and node_id not in self.anchors:
                problems.append(
                    Problem(
                        code="support.no_predecessor",
                        message=(
                            f"checked node {node_id!r} has no anchor, support, or unavailable leaf"
                        ),
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(node_id,),
                        suggested_repair=(
                            "Add support records, mark a root anchor, or declare an "
                            "unavailable leaf with policy."
                        ),
                    )
                )
            stack.remove(node_id)

        visit(record_id)
        problems.extend(self.detect_cycles())
        return SupportClosure(
            root_id=record_id,
            nodes=tuple(sorted(visited)),
            anchors=tuple(sorted(anchors)),
            unavailable_leaves=tuple(sorted(unavailable)),
            problems=tuple(problems),
        )

    def _check_frontier_item(
        self,
        target_id: str,
        item: FrontierItem,
        problems: list[Problem],
        unavailable: set[str],
    ) -> None:
        if item.node_id in self.unavailable:
            unavailable.add(item.node_id)
            if item.unavailable_policy == UnavailablePolicy.BLOCK:
                problems.append(
                    Problem(
                        code="support.unavailable_blocks",
                        message=f"required unavailable leaf {item.node_id!r} blocks closure",
                        severity=ProblemSeverity.BLOCKER,
                        related_record_ids=(target_id, item.node_id),
                    )
                )
            return
        if item.node_id in self.anchors:
            roles = self.anchor_roles.get(item.node_id)
            if roles is not None and item.role not in roles:
                problems.append(
                    Problem(
                        code="support.anchor_role_mismatch",
                        message="anchor is not compatible with the requested support role",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(target_id, item.node_id),
                    )
                )
            return
        role_edges = self.incoming(target_id, item.role)
        if not any(edge.source_id == item.node_id for edge in role_edges):
            problems.append(
                Problem(
                    code="support.frontier_unsupported",
                    message=f"frontier item {item.node_id!r} lacks role-compatible support",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(target_id, item.node_id),
                    suggested_repair="Add a support edge with the frontier item's support role.",
                )
            )

    def validate(self, event_order: EventOrder | None = None) -> tuple[Problem, ...]:
        problems: list[Problem] = []
        problems.extend(self.detect_missing_references())
        problems.extend(self.detect_cycles())
        problems.extend(self.detect_order_violations(event_order))
        for node_id in self.checked_nodes:
            problems.extend(self.closure(node_id).problems)
        return tuple(_unique_problems(problems))

    def to_dict(self) -> JsonDict:
        return {
            "nodes": {record_id: record.to_dict() for record_id, record in self.nodes.items()},
            "edges": [edge.to_dict() for edge in self.edges],
            "anchors": list(self.anchors),
            "unavailable": dict(self.unavailable),
            "checked_nodes": list(self.checked_nodes),
            "frontier_items": {
                target: [item.to_dict() for item in items]
                for target, items in self.frontier_items.items()
            },
            "validation_coordinates": {
                node_id: coordinate.to_dict()
                for node_id, coordinate in self.validation_coordinates.items()
            },
            "anchor_roles": {
                node_id: [role.value for role in roles]
                for node_id, roles in self.anchor_roles.items()
            },
            "allow_cycles": self.allow_cycles,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SupportGraph:
        nodes_raw = data.get("nodes", {})
        if not isinstance(nodes_raw, dict):
            nodes_raw = {}
        frontier_raw = data.get("frontier_items", {})
        if not isinstance(frontier_raw, dict):
            frontier_raw = {}
        coordinates_raw = data.get("validation_coordinates", {})
        if not isinstance(coordinates_raw, dict):
            coordinates_raw = {}
        anchor_roles_raw = data.get("anchor_roles", {})
        if not isinstance(anchor_roles_raw, dict):
            anchor_roles_raw = {}
        return cls(
            nodes={
                str(record_id): LedgerRecord.from_dict(record)
                for record_id, record in nodes_raw.items()
                if isinstance(record, dict)
            },
            edges=tuple(
                SupportEdge.from_dict(item)
                for item in data.get("edges", ())
                if isinstance(item, dict)
            ),
            anchors=tuple(str(item) for item in data.get("anchors", ())),
            unavailable={
                str(key): str(value) for key, value in data.get("unavailable", {}).items()
            },
            checked_nodes=tuple(str(item) for item in data.get("checked_nodes", ())),
            frontier_items={
                str(target): tuple(
                    FrontierItem.from_dict(item) for item in items if isinstance(item, dict)
                )
                for target, items in frontier_raw.items()
                if isinstance(items, list)
            },
            validation_coordinates={
                str(node_id): ValidationCoordinate.from_dict(coordinate)
                for node_id, coordinate in coordinates_raw.items()
                if isinstance(coordinate, dict)
            },
            anchor_roles={
                str(node_id): tuple(SupportRole(item) for item in roles)
                for node_id, roles in anchor_roles_raw.items()
                if isinstance(roles, list)
            },
            allow_cycles=bool(data.get("allow_cycles", False)),
        )


def _unique_problems(problems: list[Problem]) -> tuple[Problem, ...]:
    seen: set[tuple[str, tuple[str, ...], str]] = set()
    unique: list[Problem] = []
    for problem in problems:
        key = (problem.code, problem.related_record_ids, problem.message)
        if key not in seen:
            seen.add(key)
            unique.append(problem)
    return tuple(unique)
