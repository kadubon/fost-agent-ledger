from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import ModeName, Status
from .errors import UnknownModeError
from .model import JsonDict, JsonModel


@dataclass(frozen=True)
class ModeContract(JsonModel):
    """Finite contract declaring what a mode needs before use.

    The contract does not decide truth. It declares which ledger coordinates must be visible and
    respected before an output/action can be treated as admissible for the mode.
    """

    name: str
    admissible_status_region: tuple[Status, ...]
    forbidden_failures: tuple[str, ...] = ()
    required_read_coordinates: tuple[str, ...] = ()
    required_respect_coordinates: tuple[str, ...] = ()
    gate_rules: JsonDict = field(default_factory=dict)
    issue_selection_rules: JsonDict = field(default_factory=dict)
    obligation_selection_rules: JsonDict = field(default_factory=dict)
    environment_token_selection_rules: tuple[str, ...] = ()
    critic_role_requirements: tuple[str, ...] = ()
    impact_requirements: JsonDict = field(default_factory=dict)
    adequacy_rules: tuple[str, ...] = (
        "nonvacuity",
        "critic",
        "environment",
        "scope",
        "impact",
        "modeclosure",
        "compression",
        "root_debt",
        "obligation",
    )
    reason: str = ""

    @classmethod
    def draft(cls) -> ModeContract:
        return cls(
            name=ModeName.DRAFT.value,
            admissible_status_region=(Status.SUPPORTED, Status.PARTIAL, Status.UNKNOWN),
            required_read_coordinates=("claims",),
            required_respect_coordinates=("support", "issues"),
            reason="Draft mode permits visible partial support, but does not erase issues.",
        )

    @classmethod
    def research_summary(cls) -> ModeContract:
        return cls(
            name=ModeName.RESEARCH_SUMMARY.value,
            admissible_status_region=(Status.SUPPORTED, Status.PARTIAL),
            required_read_coordinates=("claims", "support", "issues", "obligations"),
            required_respect_coordinates=("support", "issues", "obligations", "certificates"),
            critic_role_requirements=("external_challenge",),
            reason="Research summaries require support visibility and unresolved caveats.",
        )

    @classmethod
    def code_generation(cls) -> ModeContract:
        return cls(
            name=ModeName.CODE_GENERATION.value,
            admissible_status_region=(Status.SUPPORTED,),
            required_read_coordinates=("claims", "support", "environment", "obligations"),
            required_respect_coordinates=(
                "support",
                "issues",
                "obligations",
                "environment",
                "certificates",
            ),
            environment_token_selection_rules=("tool_state", "policy_version"),
            reason="Code generation needs tool/policy assumptions and open obligation visibility.",
        )

    @classmethod
    def safety_sensitive_advice(cls) -> ModeContract:
        return cls(
            name=ModeName.SAFETY_SENSITIVE_ADVICE.value,
            admissible_status_region=(Status.SUPPORTED,),
            forbidden_failures=("overclaim", "certificate_misuse", "environment_drift"),
            required_read_coordinates=("claims", "support", "environment", "impact"),
            required_respect_coordinates=(
                "support",
                "issues",
                "obligations",
                "environment",
                "impact",
                "certificates",
            ),
            environment_token_selection_rules=("freshness", "policy_version"),
            critic_role_requirements=("external_challenge",),
            impact_requirements={"required": True},
            reason=(
                "Safety-sensitive advice treats unknown impact or stale assumptions as blocking."
            ),
        )

    @classmethod
    def publication(cls) -> ModeContract:
        return cls(
            name=ModeName.PUBLICATION.value,
            admissible_status_region=(Status.SUPPORTED,),
            forbidden_failures=("overclaim", "false_compression", "residue_erasure"),
            required_read_coordinates=("claims", "support", "issues", "scope", "compression"),
            required_respect_coordinates=(
                "support",
                "issues",
                "scope_exclusion",
                "mode_closure",
                "compression",
            ),
            critic_role_requirements=("external_challenge",),
            impact_requirements={"required": True},
            reason="Publication requires non-vacuous support and explicit scope exclusions.",
        )

    @classmethod
    def agent_action(cls) -> ModeContract:
        return cls(
            name=ModeName.AGENT_ACTION.value,
            admissible_status_region=(Status.SUPPORTED,),
            forbidden_failures=("over_execution", "environment_drift", "monitor_failure"),
            required_read_coordinates=("claims", "support", "environment", "obligations", "impact"),
            required_respect_coordinates=(
                "support",
                "gate",
                "obligations",
                "environment",
                "impact",
                "certificates",
            ),
            environment_token_selection_rules=("tool_state", "freshness", "boundary"),
            critic_role_requirements=("external_challenge",),
            impact_requirements={"required": True},
            reason="Agent actions require checked environment, gate, and obligation coordinates.",
        )

    @classmethod
    def self_modification(cls) -> ModeContract:
        return cls(
            name=ModeName.SELF_MODIFICATION.value,
            admissible_status_region=(Status.SUPPORTED,),
            forbidden_failures=("kernel_self_certification", "invalid_kernel_admission"),
            required_read_coordinates=("kernel", "support", "transition", "lineage"),
            required_respect_coordinates=("kernel", "transition", "certificates", "root_debt"),
            critic_role_requirements=("external_challenge",),
            impact_requirements={"required": True},
            reason=(
                "Self-modification requires lineage, prior-kernel support, "
                "and transition witnesses."
            ),
        )

    @classmethod
    def for_name(
        cls,
        name: str | ModeContract,
        *,
        allow_unknown_as_draft: bool = False,
    ) -> ModeContract:
        if isinstance(name, ModeContract):
            return name
        normalized = name.replace("-", "_").lower()
        factories = {
            ModeName.DRAFT.value: cls.draft,
            ModeName.RESEARCH_SUMMARY.value: cls.research_summary,
            ModeName.CODE_GENERATION.value: cls.code_generation,
            ModeName.SAFETY_SENSITIVE_ADVICE.value: cls.safety_sensitive_advice,
            ModeName.PUBLICATION.value: cls.publication,
            ModeName.AGENT_ACTION.value: cls.agent_action,
            ModeName.SELF_MODIFICATION.value: cls.self_modification,
        }
        factory = factories.get(normalized)
        if factory is not None:
            return factory()
        if allow_unknown_as_draft:
            contract = cls.draft()
            return cls(
                name=normalized,
                admissible_status_region=contract.admissible_status_region,
                forbidden_failures=contract.forbidden_failures,
                required_read_coordinates=contract.required_read_coordinates,
                required_respect_coordinates=contract.required_respect_coordinates,
                gate_rules=contract.gate_rules,
                issue_selection_rules=contract.issue_selection_rules,
                obligation_selection_rules=contract.obligation_selection_rules,
                environment_token_selection_rules=contract.environment_token_selection_rules,
                critic_role_requirements=contract.critic_role_requirements,
                impact_requirements=contract.impact_requirements,
                adequacy_rules=contract.adequacy_rules,
                reason=(
                    "Unknown mode explicitly evaluated under draft fallback; "
                    "do not treat this as a mode-specific guarantee."
                ),
            )
        raise UnknownModeError(f"unknown mode contract: {name!r}")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModeContract:
        return cls(
            name=str(data["name"]),
            admissible_status_region=tuple(
                Status(item) for item in data.get("admissible_status_region", ())
            ),
            forbidden_failures=tuple(str(item) for item in data.get("forbidden_failures", ())),
            required_read_coordinates=tuple(
                str(item) for item in data.get("required_read_coordinates", ())
            ),
            required_respect_coordinates=tuple(
                str(item) for item in data.get("required_respect_coordinates", ())
            ),
            gate_rules=dict(data.get("gate_rules", {})),
            issue_selection_rules=dict(data.get("issue_selection_rules", {})),
            obligation_selection_rules=dict(data.get("obligation_selection_rules", {})),
            environment_token_selection_rules=tuple(
                str(item) for item in data.get("environment_token_selection_rules", ())
            ),
            critic_role_requirements=tuple(
                str(item) for item in data.get("critic_role_requirements", ())
            ),
            impact_requirements=dict(data.get("impact_requirements", {})),
            adequacy_rules=tuple(str(item) for item in data.get("adequacy_rules", ())),
            reason=str(data.get("reason", "")),
        )


def default_mode_contracts() -> tuple[ModeContract, ...]:
    return (
        ModeContract.draft(),
        ModeContract.research_summary(),
        ModeContract.code_generation(),
        ModeContract.safety_sensitive_advice(),
        ModeContract.publication(),
        ModeContract.agent_action(),
        ModeContract.self_modification(),
    )
