from __future__ import annotations

from ..ledger import EvaluatedLedger
from ..model import Problem
from ..modes import ModeContract
from ..transitions import LedgerTransition, validate_transition


def validate_transition_records(
    before: EvaluatedLedger,
    after: EvaluatedLedger,
    transition: LedgerTransition | None = None,
    *,
    mode: ModeContract | str | None = None,
) -> tuple[Problem, ...]:
    return validate_transition(before, after, transition, mode=mode)
