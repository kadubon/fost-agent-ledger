from __future__ import annotations

import runpy
from pathlib import Path

import pytest

from fost_agent_ledger import LedgerBuilder
from fost_agent_ledger.cli import main


def test_cli_schema_and_validate(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["schema"]) == 0
    captured = capsys.readouterr()
    assert "LedgerRecord" in captured.out

    builder = LedgerBuilder(agent_id="agent-1", mode="draft")
    claim = builder.add_claim("A CLI claim.")
    builder.add_support("A support record.", supports=[claim.id])
    path = tmp_path / "ledger.json"
    path.write_text(builder.finalize().to_json(), encoding="utf-8")
    assert main(["validate", str(path)]) == 0
    assert main(["summarize", str(path)]) == 0
    assert main(["diff", str(path), str(path)]) == 0
    assert main(["demo"]) == 0


def test_examples_execute() -> None:
    for path in Path("examples").glob("*.py"):
        runpy.run_path(str(path), run_name="__main__")
