from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import IssueSeverity
from .ids import new_id
from .model import JsonDict, JsonModel


@dataclass(frozen=True)
class Issue(JsonModel):
    issue_id: str
    text: str
    severity: IssueSeverity = IssueSeverity.MEDIUM
    blocking: bool = False
    resolved: bool = False
    reason: str = ""
    support_refs: tuple[str, ...] = ()
    metadata: JsonDict = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        text: str,
        *,
        severity: IssueSeverity | str = IssueSeverity.MEDIUM,
        blocking: bool = False,
        resolved: bool = False,
        reason: str = "",
        support_refs: tuple[str, ...] = (),
    ) -> Issue:
        return cls(
            issue_id=new_id("issue"),
            text=text,
            severity=IssueSeverity(severity),
            blocking=blocking,
            resolved=resolved,
            reason=reason,
            support_refs=support_refs,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Issue:
        return cls(
            issue_id=str(data["issue_id"]),
            text=str(data["text"]),
            severity=IssueSeverity(data.get("severity", IssueSeverity.MEDIUM.value)),
            blocking=bool(data.get("blocking", False)),
            resolved=bool(data.get("resolved", False)),
            reason=str(data.get("reason", "")),
            support_refs=tuple(str(item) for item in data.get("support_refs", ())),
            metadata=dict(data.get("metadata", {})),
        )


def issue_is_open(issue: Issue) -> bool:
    return not issue.resolved
