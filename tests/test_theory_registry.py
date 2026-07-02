from __future__ import annotations

import importlib
import os
from collections import Counter
from pathlib import Path

from fost_agent_ledger import __version__, iter_theory_coverage, load_theory_registry
from fost_agent_ledger.builder import LedgerBuilder
from fost_agent_ledger.enums import RecordType
from fost_agent_ledger.payloads import PAYLOAD_TYPES
from fost_agent_ledger.problem_codes import PROBLEM_EXPLANATIONS
from fost_agent_ledger.serialization import export_json_schema
from tools.audit_theory_registry import audit_registry

DOI = "https://doi.org/10.5281/zenodo.20995846"


def test_theory_registry_is_tex_derived_complete_and_independent() -> None:
    registry = load_theory_registry()
    docs_registry = Path("docs/theory_items.json").read_text(encoding="utf-8")
    package_registry = Path("src/fost_agent_ledger/theory_items.json").read_text(encoding="utf-8")
    rows = iter_theory_coverage()
    assert docs_registry == package_registry
    assert registry["doi"] == DOI
    assert registry["registry_version"] == "2.0.0"
    assert registry["item_count"] == 184
    assert len(rows) == 184
    assert {row.coverage for row in rows} == {"implemented"}
    assert all(row.runtime_anchor for row in rows)
    assert all(row.test_anchor for row in rows)
    assert all(row.coverage_reason for row in rows)
    assert all(row.anchor_refs for row in rows)
    assert registry["section_count"] == 22
    assert len(registry["appendix_sections"]) == 10
    assert "Bounded Rationality and Assurance" in registry["appendix_sections"]

    counts = Counter(row.environment for row in rows)
    assert counts == {
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


def test_theory_registry_anchors_are_machine_checkable() -> None:
    registry = load_theory_registry()
    defs = export_json_schema()["$defs"]
    for item in registry["items"]:
        anchors = item["anchor_refs"]
        for module_name in anchors["runtime_modules"]:
            importlib.import_module(module_name)
        for symbol_name in anchors["runtime_symbols"]:
            module_name, _, attribute_name = symbol_name.rpartition(".")
            module = importlib.import_module(module_name)
            assert hasattr(module, attribute_name), symbol_name
        for schema_def in anchors["schema_defs"]:
            assert schema_def in defs
        for problem_code in anchors["problem_codes"]:
            assert problem_code in PROBLEM_EXPLANATIONS
        for doc_path in anchors["doc_paths"]:
            assert Path(doc_path).is_file(), doc_path
        for test_path in anchors["test_paths"]:
            assert Path(test_path).is_file(), test_path


def test_theory_registry_anchors_are_not_generic_only() -> None:
    generic_symbols = {
        "fost_agent_ledger.theory.TheoryCoverageRow",
        "fost_agent_ledger.model.LedgerRecord",
        "fost_agent_ledger.model.Problem",
        "fost_agent_ledger.serialization.schema.export_json_schema",
    }
    generic_schema_defs = {
        "LedgerRecord",
        "EvaluatedLedger",
        "Problem",
        "TheoryItemCoveragePayload",
    }
    for item in load_theory_registry()["items"]:
        anchors = item["anchor_refs"]
        assert set(anchors["runtime_symbols"]) - generic_symbols, item["id"]
        assert set(anchors["schema_defs"]) - generic_schema_defs, item["id"]
        assert set(anchors["doc_paths"]) - {"docs/theory_mapping.md"}, item["id"]


def test_optional_tex_audit_matches_registry_when_requested() -> None:
    tex_path = os.environ.get("FOST_TEX_PATH")
    registry_path = Path("docs/theory_items.json")
    assert audit_registry(registry_path) == []
    if tex_path:
        assert audit_registry(registry_path, Path(tex_path)) == []


def test_theory_mapping_is_registry_synced() -> None:
    mapping = Path("docs/theory_mapping.md").read_text(encoding="utf-8")
    rows = iter_theory_coverage()
    for row in rows:
        expected = (
            f"| {row.item_id} | {row.title} | {row.environment} | {row.section} | "
            f"{row.coverage} | {row.runtime_anchor} | {row.test_anchor} |"
        )
        assert expected in mapping
    assert mapping.count("| implemented |") == 184
    assert "| partial |" not in mapping
    assert "| out-of-scope |" not in mapping


def test_docs_boundaries_and_doi_are_current() -> None:
    docs = {
        "README.md": Path("README.md").read_text(encoding="utf-8"),
        "docs/index.md": Path("docs/index.md").read_text(encoding="utf-8"),
        "docs/design.md": Path("docs/design.md").read_text(encoding="utf-8"),
        "docs/limitations.md": Path("docs/limitations.md").read_text(encoding="utf-8"),
        "docs/theory_mapping.md": Path("docs/theory_mapping.md").read_text(encoding="utf-8"),
    }
    assert all(DOI in text for text in docs.values())
    assert '"schema_version": "0.3"' not in "\n".join(docs.values())
    assert "complete implementation" in docs["docs/design.md"]
    assert "not an implementation gap" in docs["docs/limitations.md"]


def test_schema_payload_builder_and_problem_docs_are_synced() -> None:
    defs = export_json_schema()["$defs"]
    missing_payload_defs = {
        payload_type.__name__
        for record_type, payload_type in PAYLOAD_TYPES.items()
        if payload_type.__name__ not in defs
        and record_type not in {RecordType.CLAIM, RecordType.SUPPORT}
    }
    assert missing_payload_defs == set()

    for helper_name in (
        "add_process_class",
        "add_distinction_basis",
        "add_presentation",
        "add_requirement_policy",
        "add_settledness_license",
        "add_obstruction_profile",
        "add_certificate_cover",
        "add_obligation_discharge",
        "add_compression_factorization",
        "add_self_modification_witness",
    ):
        assert hasattr(LedgerBuilder, helper_name)

    problem_docs = Path("docs/problem_codes.md").read_text(encoding="utf-8")
    for code in PROBLEM_EXPLANATIONS:
        assert code in problem_docs


def test_version_is_v100_with_schema_v10() -> None:
    assert __version__ == "2.0.0"
    schema = export_json_schema()
    assert schema["$id"].endswith("fost-agent-ledger-2.0.schema.json")
    assert schema["$defs"]["EvaluatedLedger"]["properties"]["schema_version"]["const"] == "2.0"
