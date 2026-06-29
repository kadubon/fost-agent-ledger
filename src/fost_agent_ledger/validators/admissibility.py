from __future__ import annotations

from ..admissibility import validate_ledger
from ..ledger import EvaluatedLedger
from ..model import Problem
from ..modes import ModeContract


def validate_admissibility(
    ledger: EvaluatedLedger,
    mode: ModeContract | str | None = None,
) -> tuple[Problem, ...]:
    result = validate_ledger(ledger, mode=mode)
    return result.errors + result.warnings
