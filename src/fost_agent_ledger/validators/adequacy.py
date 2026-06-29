from __future__ import annotations

from ..adequacy import validate_adequacy
from ..ledger import EvaluatedLedger
from ..model import Problem
from ..modes import ModeContract


def validate_contract_adequacy(
    ledger: EvaluatedLedger,
    mode: ModeContract | str | None = None,
) -> tuple[Problem, ...]:
    return validate_adequacy(ledger, ModeContract.for_name(mode or ledger.mode)).problems
