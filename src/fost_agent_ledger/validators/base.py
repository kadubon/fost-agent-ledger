from __future__ import annotations

from collections.abc import Callable

from ..ledger import EvaluatedLedger
from ..model import Problem

ValidatorFn = Callable[[EvaluatedLedger], tuple[Problem, ...]]
