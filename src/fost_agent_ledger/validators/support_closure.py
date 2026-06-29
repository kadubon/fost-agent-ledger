from __future__ import annotations

from ..ledger import EvaluatedLedger
from ..model import Problem


def validate_support_closure(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    return ledger.support_graph.validate()
