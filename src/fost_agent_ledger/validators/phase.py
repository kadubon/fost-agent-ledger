from __future__ import annotations

from ..admissibility import _validate_stage_separation
from ..ledger import EvaluatedLedger
from ..model import Problem


def validate_phase_order(ledger: EvaluatedLedger) -> tuple[Problem, ...]:
    return _validate_stage_separation(ledger)
