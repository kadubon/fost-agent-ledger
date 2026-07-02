from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .enums import EnvironmentTokenKind, ProblemSeverity, TokenState
from .ids import new_id
from .model import JsonDict, JsonModel, Problem, parse_datetime


@dataclass(frozen=True)
class EnvironmentToken(JsonModel):
    token_id: str
    kind: EnvironmentTokenKind
    name: str
    state: TokenState = TokenState.UNKNOWN
    selected: bool = False
    known_relevant: bool = False
    scope: JsonDict = field(default_factory=dict)
    freshness_at: datetime | None = None
    reason: str = ""
    metadata: JsonDict = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        kind: EnvironmentTokenKind | str,
        name: str,
        state: TokenState | str = TokenState.UNKNOWN,
        selected: bool = False,
        known_relevant: bool = False,
        reason: str = "",
    ) -> EnvironmentToken:
        return cls(
            token_id=new_id("env"),
            kind=EnvironmentTokenKind(kind),
            name=name,
            state=TokenState(state),
            selected=selected,
            known_relevant=known_relevant,
            reason=reason,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnvironmentToken:
        return cls(
            token_id=str(data["token_id"]),
            kind=EnvironmentTokenKind(data["kind"]),
            name=str(data["name"]),
            state=TokenState(data.get("state", TokenState.UNKNOWN.value)),
            selected=bool(data.get("selected", False)),
            known_relevant=bool(data.get("known_relevant", False)),
            scope=dict(data.get("scope", {})),
            freshness_at=parse_datetime(data["freshness_at"]) if data.get("freshness_at") else None,
            reason=str(data.get("reason", "")),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class EnvironmentRequirement(JsonModel):
    kind: EnvironmentTokenKind | None = None
    name: str | None = None
    reason: str = ""

    @classmethod
    def from_selector(cls, selector: str) -> EnvironmentRequirement:
        try:
            return cls(kind=EnvironmentTokenKind(selector))
        except ValueError:
            return cls(name=selector)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnvironmentRequirement:
        kind_raw = data.get("kind")
        return cls(
            kind=EnvironmentTokenKind(kind_raw) if kind_raw else None,
            name=str(data["name"]) if data.get("name") else None,
            reason=str(data.get("reason", "")),
        )

    def label(self) -> str:
        if self.kind is not None and self.name:
            return f"{self.kind.value}:{self.name}"
        if self.kind is not None:
            return self.kind.value
        return self.name or "environment"

    def matches(self, token: EnvironmentToken) -> bool:
        if self.kind is not None and token.kind != self.kind:
            return False
        return not (self.name is not None and token.name != self.name)


def validate_environment_tokens(
    tokens: tuple[EnvironmentToken, ...],
    *,
    required_names: tuple[str, ...] = (),
    required_requirements: tuple[EnvironmentRequirement, ...] = (),
    high_impact: bool = False,
) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    selected_tokens = tuple(token for token in tokens if token.selected)
    for token in tokens:
        if token.selected and token.state == TokenState.UNSELECTED:
            problems.append(
                Problem(
                    code="environment.selected_unselected_state",
                    message="selected environment token cannot have unselected state",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(token.token_id,),
                )
            )
        if token.known_relevant and not token.selected:
            problems.append(
                Problem(
                    code="environment.known_relevant_unselected",
                    message="known relevant environment token is not selected",
                    severity=ProblemSeverity.ERROR if high_impact else ProblemSeverity.WARNING,
                    related_record_ids=(token.token_id,),
                )
            )
        if (
            token.selected
            and token.kind in {EnvironmentTokenKind.FRESHNESS, EnvironmentTokenKind.DATA_AGE}
            and token.freshness_at is None
        ):
            problems.append(
                Problem(
                    code="environment.missing_freshness",
                    message="selected freshness/data-age token lacks a finite freshness time",
                    severity=ProblemSeverity.ERROR if high_impact else ProblemSeverity.WARNING,
                    related_record_ids=(token.token_id,),
                )
            )
    requirements = (
        *required_requirements,
        *(EnvironmentRequirement.from_selector(name) for name in required_names),
    )
    for requirement in requirements:
        selected_token = next(
            (token for token in selected_tokens if requirement.matches(token)),
            None,
        )
        label = requirement.label()
        if selected_token is None:
            problems.append(
                Problem(
                    code="environment.required_unselected",
                    message=f"required environment token {label!r} is not selected",
                    severity=ProblemSeverity.ERROR if high_impact else ProblemSeverity.WARNING,
                    related_record_ids=(label,),
                )
            )
            continue
        if selected_token.state in {
            TokenState.STALE,
            TokenState.FAILED,
            TokenState.DRIFT,
            TokenState.CONFLICT,
        }:
            problems.append(
                Problem(
                    code="environment.selected_non_ok",
                    message=(
                        f"selected environment token {label!r} is {selected_token.state.value}"
                    ),
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(selected_token.token_id,),
                )
            )
        if high_impact and selected_token.state == TokenState.UNKNOWN:
            problems.append(
                Problem(
                    code="environment.unknown_high_impact",
                    message=f"selected high-impact environment token {label!r} is unknown",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(selected_token.token_id,),
                )
            )
    return tuple(problems)
