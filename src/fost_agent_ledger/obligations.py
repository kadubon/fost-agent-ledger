from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .enums import DeadlineStatus, ObligationLifecycle, ProblemSeverity
from .ids import new_id, utc_now
from .model import JsonDict, JsonModel, Problem, parse_datetime

ALLOWED_OBLIGATION_TRANSITIONS: dict[ObligationLifecycle, tuple[ObligationLifecycle, ...]] = {
    ObligationLifecycle.UNDECLARED: (ObligationLifecycle.DECLARED,),
    ObligationLifecycle.DECLARED: (
        ObligationLifecycle.SCHEDULED,
        ObligationLifecycle.ACTIVE,
        ObligationLifecycle.CARRIED,
        ObligationLifecycle.TRANSFERRED,
        ObligationLifecycle.BLOCKED,
        ObligationLifecycle.FAILED,
    ),
    ObligationLifecycle.SCHEDULED: (
        ObligationLifecycle.ACTIVE,
        ObligationLifecycle.DISCHARGED,
        ObligationLifecycle.EXPIRED,
        ObligationLifecycle.FAILED,
    ),
    ObligationLifecycle.ACTIVE: (
        ObligationLifecycle.DISCHARGED,
        ObligationLifecycle.EXPIRED,
        ObligationLifecycle.FAILED,
        ObligationLifecycle.BLOCKED,
    ),
    ObligationLifecycle.CARRIED: (
        ObligationLifecycle.SCHEDULED,
        ObligationLifecycle.ACTIVE,
        ObligationLifecycle.TRANSFERRED,
        ObligationLifecycle.FAILED,
    ),
    ObligationLifecycle.TRANSFERRED: (
        ObligationLifecycle.ACCEPTED_TRANSFER,
        ObligationLifecycle.FAILED,
    ),
    ObligationLifecycle.ACCEPTED_TRANSFER: (
        ObligationLifecycle.ACTIVE,
        ObligationLifecycle.DISCHARGED,
        ObligationLifecycle.EXPIRED,
        ObligationLifecycle.FAILED,
    ),
    ObligationLifecycle.BLOCKED: (ObligationLifecycle.ACTIVE, ObligationLifecycle.FAILED),
    ObligationLifecycle.EXPIRED: (ObligationLifecycle.FAILED,),
    ObligationLifecycle.DISCHARGED: (ObligationLifecycle.DISCHARGED,),
    ObligationLifecycle.FAILED: (ObligationLifecycle.FAILED,),
    ObligationLifecycle.CONFLICT: (ObligationLifecycle.CONFLICT,),
}

OPEN_LIFECYCLES = {
    ObligationLifecycle.DECLARED,
    ObligationLifecycle.SCHEDULED,
    ObligationLifecycle.ACTIVE,
    ObligationLifecycle.CARRIED,
    ObligationLifecycle.TRANSFERRED,
    ObligationLifecycle.BLOCKED,
    ObligationLifecycle.CONFLICT,
    ObligationLifecycle.EXPIRED,
    ObligationLifecycle.FAILED,
    ObligationLifecycle.UNDECLARED,
}


@dataclass(frozen=True)
class Obligation(JsonModel):
    obligation_id: str
    text: str
    lifecycle: ObligationLifecycle = ObligationLifecycle.DECLARED
    hard: bool = False
    owner: str | None = None
    due_at: datetime | None = None
    reason: str = ""
    support_refs: tuple[str, ...] = ()
    metadata: JsonDict = field(default_factory=dict)

    @property
    def is_open(self) -> bool:
        return self.lifecycle in OPEN_LIFECYCLES

    @classmethod
    def create(
        cls,
        text: str,
        *,
        lifecycle: ObligationLifecycle | str = ObligationLifecycle.DECLARED,
        hard: bool = False,
        owner: str | None = None,
        due_at: datetime | None = None,
        reason: str = "",
        support_refs: tuple[str, ...] = (),
    ) -> Obligation:
        return cls(
            obligation_id=new_id("obl"),
            text=text,
            lifecycle=ObligationLifecycle(lifecycle),
            hard=hard,
            owner=owner,
            due_at=due_at,
            reason=reason,
            support_refs=support_refs,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Obligation:
        return cls(
            obligation_id=str(data["obligation_id"]),
            text=str(data["text"]),
            lifecycle=ObligationLifecycle(data.get("lifecycle", "declared")),
            hard=bool(data.get("hard", False)),
            owner=data.get("owner"),
            due_at=parse_datetime(data["due_at"]) if data.get("due_at") else None,
            reason=str(data.get("reason", "")),
            support_refs=tuple(str(item) for item in data.get("support_refs", ())),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class ObligationLifecycleRecord(JsonModel):
    obligation_id: str
    source: ObligationLifecycle
    target: ObligationLifecycle
    event_id: str
    deadline_status: DeadlineStatus = DeadlineStatus.NOT_APPLICABLE
    reason: str = ""
    record_id: str = field(default_factory=lambda: new_id("obl-life"))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ObligationLifecycleRecord:
        return cls(
            record_id=str(data.get("record_id", new_id("obl-life"))),
            obligation_id=str(data["obligation_id"]),
            source=ObligationLifecycle(data["source"]),
            target=ObligationLifecycle(data["target"]),
            event_id=str(data.get("event_id", "event-0")),
            deadline_status=DeadlineStatus(
                data.get("deadline_status", DeadlineStatus.NOT_APPLICABLE.value)
            ),
            reason=str(data.get("reason", "")),
        )


def validate_obligations(obligations: tuple[Obligation, ...]) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    now = utc_now()
    for obligation in obligations:
        if obligation.hard and obligation.is_open:
            problems.append(
                Problem(
                    code="obligation.hard_open",
                    message="hard obligation remains open",
                    severity=ProblemSeverity.BLOCKER,
                    related_record_ids=(obligation.obligation_id,),
                    suggested_repair=(
                        "Schedule, discharge, transfer with acceptance, or explicitly "
                        "block the output."
                    ),
                )
            )
        if obligation.lifecycle == ObligationLifecycle.SCHEDULED and obligation.due_at is None:
            problems.append(
                Problem(
                    code="obligation.scheduled_without_due_at",
                    message="scheduled obligation lacks a due date or event condition",
                    severity=ProblemSeverity.WARNING,
                    related_record_ids=(obligation.obligation_id,),
                )
            )
        if obligation.due_at is not None and obligation.due_at < now and obligation.is_open:
            problems.append(
                Problem(
                    code="obligation.expired_open",
                    message="open obligation is past its due date",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(obligation.obligation_id,),
                )
            )
        if obligation.lifecycle == ObligationLifecycle.DISCHARGED and not obligation.support_refs:
            problems.append(
                Problem(
                    code="obligation.discharge_without_support",
                    message="obligation discharge must cite finite support",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(obligation.obligation_id,),
                )
            )
    return tuple(problems)


def validate_lifecycle_record(record: ObligationLifecycleRecord) -> tuple[Problem, ...]:
    allowed = ALLOWED_OBLIGATION_TRANSITIONS.get(record.source, ())
    if record.target in allowed:
        return ()
    return (
        Problem(
            code="obligation.invalid_transition",
            message=(
                "obligation lifecycle cannot move from "
                f"{record.source.value} to {record.target.value}"
            ),
            severity=ProblemSeverity.ERROR,
            related_record_ids=(record.record_id, record.obligation_id),
        ),
    )
