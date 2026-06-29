from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

THEORY_ENVIRONMENTS = (
    "principle",
    "remark",
    "definition",
    "observation",
    "lemma",
    "theorem",
    "corollary",
    "boundarylemma",
    "proposition",
    "example",
)

EXPECTED_COUNTS = {
    "principle": 10,
    "remark": 3,
    "definition": 99,
    "observation": 6,
    "lemma": 2,
    "theorem": 3,
    "corollary": 3,
    "boundarylemma": 2,
    "proposition": 52,
    "example": 4,
}

GENERIC_SYMBOLS = {
    "fost_agent_ledger.theory.TheoryCoverageRow",
    "fost_agent_ledger.model.LedgerRecord",
    "fost_agent_ledger.model.Problem",
    "fost_agent_ledger.serialization.schema.export_json_schema",
}
GENERIC_SCHEMA_DEFS = {
    "LedgerRecord",
    "EvaluatedLedger",
    "Problem",
    "TheoryItemCoveragePayload",
}
PROPERTY_ENVIRONMENTS = {
    "observation",
    "lemma",
    "theorem",
    "corollary",
    "boundarylemma",
    "proposition",
}


@dataclass(frozen=True)
class ExtractedTheoryItem:
    environment: str
    title: str
    label: str


def extract_tex_items(tex_text: str) -> tuple[ExtractedTheoryItem, ...]:
    pattern = re.compile(
        r"\\begin\{(" + "|".join(THEORY_ENVIRONMENTS) + r")\}(?:\[([^\]]*)\])?(.*?)\\end\{\1\}",
        re.DOTALL,
    )
    items: list[ExtractedTheoryItem] = []
    for match in pattern.finditer(tex_text):
        label_match = re.search(r"\\label\{([^}]+)\}", match.group(3))
        items.append(
            ExtractedTheoryItem(
                environment=match.group(1),
                title=(match.group(2) or "").strip(),
                label=label_match.group(1) if label_match else "",
            )
        )
    return tuple(items)


def audit_registry(registry_path: Path, tex_path: Path | None = None) -> list[str]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(registry, dict):
        return ["registry root is not a JSON object"]
    items = registry.get("items")
    if not isinstance(items, list):
        return ["registry has no item list"]

    errors: list[str] = []
    if registry.get("item_count") != 184 or len(items) != 184:
        errors.append("registry must contain exactly 184 theory items")
    if Counter(str(item.get("environment")) for item in items) != EXPECTED_COUNTS:
        errors.append("registry environment counts do not match the manuscript extraction")
    if {item.get("coverage") for item in items} != {"implemented"}:
        errors.append("all registry rows must be implemented")
    missing_anchors = [
        str(item.get("id", ""))
        for item in items
        if not item.get("runtime_anchor")
        or not item.get("test_anchor")
        or not item.get("coverage_reason")
        or not item.get("anchor_refs")
    ]
    if missing_anchors:
        errors.append(f"registry rows have missing anchors: {', '.join(missing_anchors)}")

    errors.extend(_audit_anchor_profiles(items))

    if tex_path is not None:
        extracted = extract_tex_items(tex_path.read_text(encoding="utf-8"))
        registry_triples = tuple(
            ExtractedTheoryItem(
                environment=str(item.get("environment", "")),
                title=str(item.get("title", "")),
                label=str(item.get("label", "")),
            )
            for item in items
        )
        if extracted != registry_triples:
            errors.append("TeX extraction does not match registry item order/title/label triples")
    return errors


def _audit_anchor_profiles(items: list[object]) -> list[str]:
    errors: list[str] = []
    for raw_item in items:
        if not isinstance(raw_item, dict):
            errors.append("registry item is not a JSON object")
            continue
        item_id = str(raw_item.get("id", ""))
        environment = str(raw_item.get("environment", ""))
        anchors = raw_item.get("anchor_refs", {})
        if not isinstance(anchors, dict):
            errors.append(f"{item_id}: anchor_refs is not an object")
            continue
        runtime_symbols = _string_set(anchors.get("runtime_symbols"))
        schema_defs = _string_set(anchors.get("schema_defs"))
        doc_paths = _string_set(anchors.get("doc_paths"))
        test_paths = _string_set(anchors.get("test_paths"))
        if not runtime_symbols - GENERIC_SYMBOLS:
            errors.append(f"{item_id}: runtime anchor is generic-only")
        if not schema_defs - GENERIC_SCHEMA_DEFS:
            errors.append(f"{item_id}: schema anchor is generic-only")
        if doc_paths <= {"docs/theory_mapping.md"}:
            errors.append(f"{item_id}: docs anchor is generic-only")
        for doc_path in doc_paths:
            if not Path(doc_path).is_file():
                errors.append(f"{item_id}: missing doc path {doc_path}")
        for test_path in test_paths:
            if not Path(test_path).is_file():
                errors.append(f"{item_id}: missing test path {test_path}")

        if environment in {"principle", "remark"} and (
            "docs/design.md" not in doc_paths or "docs/limitations.md" not in doc_paths
        ):
            errors.append(f"{item_id}: boundary item lacks design-boundary docs")
        if environment == "definition" and not any(
            name.endswith("Payload") for name in schema_defs
        ):
            errors.append(f"{item_id}: definition lacks a typed payload schema anchor")
        if environment in PROPERTY_ENVIRONMENTS:
            validators = {
                "fost_agent_ledger.formal.validate_formal_completion",
                "fost_agent_ledger.admissibility.validate_ledger",
            }
            if not runtime_symbols & validators:
                errors.append(f"{item_id}: property item lacks validator anchor")
            if not test_paths:
                errors.append(f"{item_id}: property item lacks test anchor")
        if environment == "example":
            required_symbols = {
                "fost_agent_ledger.builder.LedgerBuilder",
                "fost_agent_ledger.cli.main",
            }
            if not required_symbols <= runtime_symbols:
                errors.append(f"{item_id}: example lacks builder/CLI anchors")
    return errors


def _string_set(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item) for item in value}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit the FOST theory coverage registry.")
    parser.add_argument("--registry", default="docs/theory_items.json")
    parser.add_argument("--tex", default=None, help="Optional local manuscript TeX path.")
    args = parser.parse_args(argv)

    errors = audit_registry(
        registry_path=Path(args.registry),
        tex_path=Path(args.tex) if args.tex else None,
    )
    if errors:
        for error in errors:
            print(error)
        return 1
    print("theory registry audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
