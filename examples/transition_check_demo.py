from __future__ import annotations

from dataclasses import replace

from fost_agent_ledger import LedgerBuilder
from fost_agent_ledger.transitions import TransitionWitness, diff_ledgers, validate_transition


def main() -> None:
    before_builder = LedgerBuilder(agent_id="agent-1", mode="draft")
    before_builder.add_claim("A claim with no support yet.")
    before = before_builder.finalize()

    after_builder = LedgerBuilder(agent_id="agent-1", mode="draft")
    claim = after_builder.add_claim("A claim with support.")
    support = after_builder.add_support("Support was added in the next cut.", supports=[claim.id])
    after = after_builder.finalize()

    transition = diff_ledgers(before, after)
    transition = replace(
        transition,
        witnesses=(TransitionWitness(coordinate=support.id, witness_record_id=support.id),),
    )
    problems = validate_transition(before, after, transition)
    print([problem.code for problem in problems])


if __name__ == "__main__":
    main()
