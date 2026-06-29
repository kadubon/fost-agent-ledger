from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any

from .model import JsonModel


@dataclass(frozen=True)
class TheoryCoverageRow(JsonModel):
    item_id: str
    manuscript_item: str
    coverage: str
    implementation_anchor: str
    environment: str = ""
    title: str = ""
    label: str = ""
    section: str = ""
    appendix: bool = False
    runtime_anchor: str = ""
    test_anchor: str = ""
    coverage_reason: str = ""
    anchor_refs: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_registry_item(cls, item: dict[str, Any]) -> TheoryCoverageRow:
        title = str(item["title"])
        runtime_anchor = str(item["runtime_anchor"])
        return cls(
            item_id=str(item["id"]),
            manuscript_item=title,
            coverage=str(item["coverage"]),
            implementation_anchor=runtime_anchor,
            environment=str(item.get("environment", "")),
            title=title,
            label=str(item.get("label", "")),
            section=str(item.get("section", "")),
            appendix=bool(item.get("appendix", False)),
            runtime_anchor=runtime_anchor,
            test_anchor=str(item.get("test_anchor", "")),
            coverage_reason=str(item.get("coverage_reason", "")),
            anchor_refs=dict(item.get("anchor_refs", {})),
        )


def iter_theory_coverage() -> tuple[TheoryCoverageRow, ...]:
    registry = load_theory_registry()
    return tuple(
        TheoryCoverageRow.from_registry_item(item)
        for item in registry.get("items", ())
        if isinstance(item, dict)
    )


def load_theory_registry() -> dict[str, Any]:
    """Load the TeX-derived coverage registry from package data.

    The docs table is deliberately not the source of truth. The packaged registry is
    generated from the manuscript item extraction and carries runtime/test anchors.
    """

    try:
        text = (
            resources.files("fost_agent_ledger")
            .joinpath("theory_items.json")
            .read_text(encoding="utf-8")
        )
    except FileNotFoundError:
        text = _development_registry_path().read_text(encoding="utf-8")
    loaded = json.loads(text)
    if not isinstance(loaded, dict):
        msg = "theory_items.json must contain a JSON object"
        raise ValueError(msg)
    return loaded


def coverage_summary() -> dict[str, Any]:
    rows = iter_theory_coverage()
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.coverage] = counts.get(row.coverage, 0) + 1
    return {
        "rows": len(rows),
        "counts": counts,
        "complete": counts.get("partial", 0) == 0 and counts.get("out-of-scope", 0) == 0,
    }


def _development_registry_path() -> Path:
    package_root = Path(__file__).resolve().parents[2]
    return package_root / "docs" / "theory_items.json"
