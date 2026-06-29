from __future__ import annotations

from ..ledger import EvaluatedLedger
from ..model import Problem
from ..status import evaluate_status


def validate_status(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    evaluate_status(ledger)
    return ()
