from __future__ import annotations

from typing import Protocol

from ..ledger import EvaluatedLedger


class AgentAdapter(Protocol):
    def to_ledger(self) -> EvaluatedLedger:
        """Return a finite operational ledger for the adapted agent output."""
