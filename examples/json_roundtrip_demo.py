from __future__ import annotations

from fost_agent_ledger import LedgerBuilder
from fost_agent_ledger.serialization import from_json, to_json


def main() -> None:
    builder = LedgerBuilder(agent_id="agent-1", mode="draft")
    claim = builder.add_claim("JSON serialization is stable.")
    builder.add_support("The ledger can be dumped and loaded.", supports=[claim.id])
    ledger = builder.finalize()
    loaded = from_json(to_json(ledger))
    print(len(loaded.records))


if __name__ == "__main__":
    main()
