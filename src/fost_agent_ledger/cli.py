from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from .admissibility import validate_ledger
from .builder import LedgerBuilder
from .ledger import EvaluatedLedger
from .problem_codes import explain_problem
from .serialization.schema import export_json_schema
from .theory import coverage_summary, iter_theory_coverage
from .transitions import diff_ledgers, validate_transition


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fost-ledger")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate a ledger JSON file")
    validate_parser.add_argument("ledger")
    validate_parser.add_argument("--mode")

    summarize_parser = subparsers.add_parser("summarize", help="summarize a ledger JSON file")
    summarize_parser.add_argument("ledger")

    subparsers.add_parser("schema", help="print JSON Schema")

    diff_parser = subparsers.add_parser("diff", help="diff two ledger JSON files")
    diff_parser.add_argument("before")
    diff_parser.add_argument("after")
    diff_parser.add_argument("--mode")

    init_parser = subparsers.add_parser("init", help="print a minimal v1.0 ledger template")
    init_parser.add_argument("--mode", default="draft")
    init_parser.add_argument("--agent-id", default="agent-1")

    explain_parser = subparsers.add_parser("explain", help="explain a Problem.code")
    explain_parser.add_argument("code")

    subparsers.add_parser("coverage", help="print manuscript-to-runtime coverage")

    subparsers.add_parser("demo", help="print a demo ledger")

    args = parser.parse_args(argv)
    if args.command == "validate":
        ledger = _read_ledger(args.ledger)
        result = validate_ledger(ledger, mode=args.mode)
        print(result.to_json())
        return 0 if not result.errors else 1
    if args.command == "summarize":
        ledger = _read_ledger(args.ledger)
        result = validate_ledger(ledger)
        print(result.summary)
        return 0
    if args.command == "schema":
        print(json.dumps(export_json_schema(), indent=2, sort_keys=True))
        return 0
    if args.command == "diff":
        before = _read_ledger(args.before)
        after = _read_ledger(args.after)
        transition = diff_ledgers(before, after)
        problems = validate_transition(before, after, transition, mode=args.mode)
        output = {
            "transition": transition.to_dict(),
            "problems": [problem.to_dict() for problem in problems],
        }
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0 if not problems else 1
    if args.command == "init":
        print(_init_ledger(agent_id=args.agent_id, mode=args.mode).to_json())
        return 0
    if args.command == "explain":
        explanation = explain_problem(args.code)
        if explanation is None:
            print(
                json.dumps(
                    {
                        "code": args.code,
                        "error": "unknown problem code",
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 1
        print(explanation.to_json())
        return 0
    if args.command == "demo":
        print(_demo_ledger().to_json())
        return 0
    if args.command == "coverage":
        output = {
            "summary": coverage_summary(),
            "rows": [row.to_dict() for row in iter_theory_coverage()],
        }
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    return 2


def _read_ledger(path: str) -> EvaluatedLedger:
    return EvaluatedLedger.from_json(Path(path).read_text(encoding="utf-8"))


def _demo_ledger() -> EvaluatedLedger:
    builder = LedgerBuilder(agent_id="agent-demo", mode="research_summary")
    claim = builder.add_claim("FOST records finite support rather than final truth.")
    builder.add_support(
        "The claim is supported by the manuscript abstract and boundary principles.",
        supports=[claim.id],
    )
    builder.add_issue("No external replication check was performed.", severity="medium")
    builder.add_obligation(
        "Recheck the summary if the manuscript version changes.",
        lifecycle="active",
        hard=False,
    )
    builder.add_critic_coverage(role="external_challenge", covered=True)
    return builder.finalize()


def _init_ledger(*, agent_id: str, mode: str) -> EvaluatedLedger:
    builder = LedgerBuilder(agent_id=agent_id, mode=mode)
    process = builder.add_process_class(
        process_id=agent_id,
        modes=(mode,),
        challenge_roles=("external_challenge",),
        reason="Template process class for finite-mode validation.",
    )
    claim = builder.add_claim("Replace this claim with the finite output being evaluated.")
    builder.add_distinction_basis(
        basis_id="basis-1",
        distinctions=("claim", "support", "scope"),
        record_ids=(claim.id,),
        reason="Template basis declares the distinctions used by the presentation.",
    )
    builder.add_finite_expression(
        expression_id="expr-1",
        text="Replace this expression with the output expression.",
        distinction_refs=("claim",),
        record_refs=(claim.id,),
        reason="Template finite expression.",
    )
    builder.add_presentation(
        presentation_id="presentation-1",
        basis_id="basis-1",
        expression_id="expr-1",
        distinction_ids=("claim", "support", "scope"),
        record_ids=(claim.id,),
        reason="Template presentation scope.",
    )
    builder.add_support("Replace with finite support for the claim.", supports=[claim.id])
    builder.add_presentation_map(
        map_id="presentation-map-1",
        presentation_id="presentation-1",
        domain_distinctions=("claim", "support", "scope"),
        mapped_distinctions=("claim", "support", "scope"),
        target_records=(claim.id,),
        reason="Template total presentation map.",
    )
    builder.add_requirement(
        "requirement-1",
        "Record at least one concrete support reason.",
        reason="Template requirement reason.",
    )
    builder.add_requirement_policy(
        policy_id="requirement-policy-1",
        process_id=process.id,
        requirements=("requirement-1",),
        reason="Template requirement policy.",
    )
    return builder.finalize()


if __name__ == "__main__":
    raise SystemExit(main())
