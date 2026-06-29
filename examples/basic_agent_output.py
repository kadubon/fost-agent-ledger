from __future__ import annotations

from fost_agent_ledger import LedgerBuilder, ModeContract, validate_ledger


def main() -> None:
    builder = LedgerBuilder(agent_id="agent-1", mode="research_summary")
    claim = builder.add_claim("FOST records finite operational support.")
    builder.add_support("Supported by the manuscript abstract.", supports=[claim.id])
    builder.add_issue("No external replication check was performed.", severity="medium")
    builder.add_obligation("Recheck if the manuscript version changes.", lifecycle="active")
    builder.add_critic_coverage(role="external_challenge", covered=True)
    result = validate_ledger(builder.finalize(), mode=ModeContract.research_summary())
    print(result.summary)


if __name__ == "__main__":
    main()
