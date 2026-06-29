from __future__ import annotations

from dataclasses import dataclass

from ..builder import LedgerBuilder
from ..ledger import EvaluatedLedger


@dataclass(frozen=True)
class SimpleAgentAdapter:
    agent_id: str
    mode: str
    output: str
    supports: tuple[str, ...] = ()
    issues: tuple[str, ...] = ()

    def to_ledger(self) -> EvaluatedLedger:
        builder = LedgerBuilder(agent_id=self.agent_id, mode=self.mode)
        claim = builder.add_claim(self.output)
        for support in self.supports:
            builder.add_support(support, supports=[claim.id])
        for issue in self.issues:
            builder.add_issue(issue)
        return builder.finalize()
