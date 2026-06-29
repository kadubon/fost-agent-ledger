from __future__ import annotations

from ..ledger import EvaluatedLedger
from . import schema as _schema  # noqa: F401


def to_json(ledger: EvaluatedLedger, *, indent: int | None = 2) -> str:
    return ledger.to_json(indent=indent)


def from_json(text: str) -> EvaluatedLedger:
    return EvaluatedLedger.from_json(text)


def to_json_lines(ledger: EvaluatedLedger) -> str:
    return ledger.to_json_lines()


def from_json_lines(
    text: str,
    *,
    agent_id: str = "unknown",
    mode: str = "draft",
) -> EvaluatedLedger:
    return EvaluatedLedger.from_json_lines(text, agent_id=agent_id, mode=mode)
