from __future__ import annotations

from fost_agent_ledger.enums import LedgerStage, RecordType, SupportRole, UnavailablePolicy
from fost_agent_ledger.model import FrontierItem, LedgerRecord, SupportEdge
from fost_agent_ledger.support import SupportGraph


def _record(record_id: str, record_type: RecordType = RecordType.SUPPORT) -> LedgerRecord:
    return LedgerRecord.create(record_type, LedgerStage.SUPPORT, {"text": record_id}, id=record_id)


def test_support_closure_with_anchor_and_witness() -> None:
    claim = _record("claim", RecordType.CLAIM)
    support = _record("support")
    graph = (
        SupportGraph()
        .add_node(claim)
        .add_node(support)
        .mark_anchor(support.id)
        .mark_checked(claim.id)
        .add_edge(
            SupportEdge(
                source_id=support.id,
                target_id=claim.id,
                role=SupportRole.DATA,
                witness_id=support.id,
            )
        )
    )
    closure = graph.closure(claim.id)
    assert closure.ok
    assert closure.anchors == ("support",)


def test_cycle_detection_blocks_support() -> None:
    a = _record("a")
    b = _record("b")
    graph = (
        SupportGraph()
        .add_node(a)
        .add_node(b)
        .mark_checked(a.id)
        .add_edge(SupportEdge(source_id=a.id, target_id=b.id, witness_id=a.id))
        .add_edge(SupportEdge(source_id=b.id, target_id=a.id, witness_id=b.id))
    )
    assert any(problem.code == "support.cycle" for problem in graph.validate())


def test_unavailable_leaf_terminates_but_is_not_evidence() -> None:
    target = _record("target")
    item = FrontierItem(
        node_id="missing-leaf",
        role=SupportRole.DATA,
        unavailable_policy=UnavailablePolicy.RECHECK,
        reason="external record unavailable",
    )
    graph = (
        SupportGraph()
        .add_node(target)
        .mark_checked(target.id)
        .mark_unavailable("missing-leaf", "not accessible")
        .add_frontier_item(target.id, item)
    )
    closure = graph.closure(target.id)
    assert closure.ok
    assert closure.unavailable_leaves == ("missing-leaf",)


def test_blocking_unavailable_leaf_reports_problem() -> None:
    target = _record("target")
    graph = (
        SupportGraph()
        .add_node(target)
        .mark_checked(target.id)
        .mark_unavailable("missing-leaf", "not accessible")
        .add_frontier_item(
            target.id,
            FrontierItem(
                node_id="missing-leaf",
                role=SupportRole.DATA,
                unavailable_policy=UnavailablePolicy.BLOCK,
            ),
        )
    )
    assert any(problem.code == "support.unavailable_blocks" for problem in graph.validate())
