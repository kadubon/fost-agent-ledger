from __future__ import annotations

from fost_agent_ledger import validate_ledger
from fost_agent_ledger.adapters import SimpleAgentAdapter


def main() -> None:
    adapter = SimpleAgentAdapter(
        agent_id="agent-1",
        mode="research_summary",
        output="The result is supported by two finite artifacts.",
        supports=("artifact A", "artifact B"),
        issues=("No independent reviewer was recorded.",),
    )
    result = validate_ledger(adapter.to_ledger())
    print(result.summary)


if __name__ == "__main__":
    main()
