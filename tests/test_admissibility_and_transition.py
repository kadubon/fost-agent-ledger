from __future__ import annotations

from fost_agent_ledger import LedgerBuilder, ModeContract, assess_output, validate_ledger
from fost_agent_ledger.enums import Admissibility, Status
from fost_agent_ledger.status import evaluate_status
from fost_agent_ledger.transitions import LedgerTransition, validate_transition


def test_research_summary_with_visible_issue_is_partial_but_admissible() -> None:
    builder = LedgerBuilder(agent_id="agent-1", mode="research_summary")
    claim = builder.add_claim("A supported summary claim.")
    builder.add_support("A finite support record.", supports=[claim.id])
    builder.add_issue("External replication is absent.")
    builder.add_critic_coverage(role="external_challenge", covered=True)
    result = validate_ledger(builder.finalize(), mode=ModeContract.research_summary())
    assert result.status == Status.PARTIAL
    assert result.admissibility == Admissibility.ADMISSIBLE


def test_anti_vacuity_failure_for_action_mode() -> None:
    builder = LedgerBuilder(agent_id="agent-1", mode="agent_action")
    builder.add_claim("Execute action.")
    result = validate_ledger(builder.finalize(), mode=ModeContract.agent_action())
    codes = {problem.code for problem in result.errors}
    assert "adequacy.vacuous" in codes
    assert result.admissibility == Admissibility.INADMISSIBLE


def test_environment_and_impact_required_for_high_impact_mode() -> None:
    builder = LedgerBuilder(agent_id="agent-1", mode="safety_sensitive_advice")
    claim = builder.add_claim("Give safety-sensitive advice.")
    builder.add_support("A finite support record.", supports=[claim.id])
    builder.add_critic_coverage(role="external_challenge", covered=True)
    result = validate_ledger(builder.finalize(), mode=ModeContract.safety_sensitive_advice())
    codes = {problem.code for problem in result.errors}
    assert "adequacy.impact_unknown" in codes
    assert "environment.required_unselected" in codes or "adequacy.environment_selection" in codes


def test_hard_obligation_blocks_admissibility() -> None:
    builder = LedgerBuilder(agent_id="agent-1", mode="draft")
    claim = builder.add_claim("Supported but blocked by a hard obligation.")
    builder.add_support("Support.", supports=[claim.id])
    builder.add_obligation("Perform mandatory audit.", lifecycle="active", hard=True)
    result = validate_ledger(builder.finalize())
    assert result.admissibility == Admissibility.BLOCKED
    assert any(problem.code == "obligation.hard_open" for problem in result.errors)


def test_status_can_be_evaluated_separately_from_admissibility() -> None:
    builder = LedgerBuilder(agent_id="agent-1", mode="publication")
    claim = builder.add_claim("A public claim.")
    builder.add_support("Support.", supports=[claim.id])
    ledger = builder.finalize()
    assert evaluate_status(ledger) == Status.SUPPORTED
    result = validate_ledger(ledger, mode=ModeContract.publication())
    assert result.admissibility == Admissibility.INADMISSIBLE


def test_untraced_admissibility_gain_is_reported() -> None:
    before_builder = LedgerBuilder(agent_id="agent-1", mode="draft")
    before_builder.add_claim("Unsupported claim.")
    before = before_builder.finalize()

    after_builder = LedgerBuilder(agent_id="agent-1", mode="draft")
    claim = after_builder.add_claim("Supported claim.")
    after_builder.add_support("Support.", supports=[claim.id])
    after = after_builder.finalize()

    transition = LedgerTransition(previous_cut_id="before", next_cut_id="after")
    problems = validate_transition(before, after, transition, mode="draft")
    assert any(problem.code == "transition.untraced_admissibility_gain" for problem in problems)


def test_assess_output_compact_api() -> None:
    result = assess_output(
        agent_id="agent-1",
        mode="draft",
        output="Output",
        supports=("Support",),
    )
    assert result.status == Status.SUPPORTED
