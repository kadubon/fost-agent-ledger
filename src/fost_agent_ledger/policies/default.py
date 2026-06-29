from __future__ import annotations

from ..admissibility import validate_ledger
from ..ledger import EvaluatedLedger
from ..model import ValidationResult
from ..modes import ModeContract


def get_default_mode_contract(mode: str) -> ModeContract:
    return ModeContract.for_name(mode)


def default_validate(
    ledger: EvaluatedLedger,
    mode: ModeContract | str | None = None,
) -> ValidationResult:
    return validate_ledger(ledger, mode=mode)
