from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .enums import (
    CERTIFICATE_USE_TO_SUPPORT_ROLE,
    CertificateStateValue,
    CertificateUseKind,
    JudgmentKind,
    ProblemSeverity,
    TargetState,
)
from .ids import new_id, utc_now
from .model import JsonDict, JsonModel, Problem, parse_datetime
from .support import SupportGraph


@dataclass(frozen=True)
class Certificate(JsonModel):
    certificate_id: str
    issuer: str
    scope: JsonDict = field(default_factory=dict)
    issued_at: datetime = field(default_factory=utc_now)
    expires_at: datetime | None = None
    metadata: JsonDict = field(default_factory=dict)

    def is_expired(self, now: datetime | None = None) -> bool:
        return self.expires_at is not None and (now or utc_now()) >= self.expires_at

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Certificate:
        return cls(
            certificate_id=str(data["certificate_id"]),
            issuer=str(data.get("issuer", "unknown")),
            scope=dict(data.get("scope", {})),
            issued_at=parse_datetime(data.get("issued_at")),
            expires_at=parse_datetime(data["expires_at"]) if data.get("expires_at") else None,
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class CertificateTarget(JsonModel):
    target_id: str
    judgment_kind: JudgmentKind
    use_kind: CertificateUseKind
    target_node: str
    event_id: str
    target_state: TargetState = TargetState.COMPLETE
    scope: JsonDict = field(default_factory=dict)
    required: bool = False
    metadata: JsonDict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CertificateTarget:
        return cls(
            target_id=str(data["target_id"]),
            judgment_kind=JudgmentKind(data["judgment_kind"]),
            use_kind=CertificateUseKind(data["use_kind"]),
            target_node=str(data["target_node"]),
            event_id=str(data.get("event_id", "event-0")),
            target_state=TargetState(data.get("target_state", TargetState.COMPLETE.value)),
            scope=dict(data.get("scope", {})),
            required=bool(data.get("required", False)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class RequiredCertificate(JsonModel):
    target_id: str
    certificate_id: str
    required: bool = True
    reason: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RequiredCertificate:
        return cls(
            target_id=str(data["target_id"]),
            certificate_id=str(data["certificate_id"]),
            required=bool(data.get("required", True)),
            reason=str(data.get("reason", "")),
        )


@dataclass(frozen=True)
class CertificateUse(JsonModel):
    use_id: str
    certificate_id: str
    target_id: str
    judgment_kind: JudgmentKind
    use_kind: CertificateUseKind
    target_node: str
    event_id: str = "event-0"
    supports: tuple[str, ...] = ()
    metadata: JsonDict = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        certificate_id: str,
        target_id: str,
        judgment_kind: JudgmentKind | str,
        use_kind: CertificateUseKind | str,
        target_node: str,
        event_id: str = "event-0",
        supports: tuple[str, ...] = (),
    ) -> CertificateUse:
        return cls(
            use_id=new_id("cert-use"),
            certificate_id=certificate_id,
            target_id=target_id,
            judgment_kind=JudgmentKind(judgment_kind),
            use_kind=CertificateUseKind(use_kind),
            target_node=target_node,
            event_id=event_id,
            supports=supports,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CertificateUse:
        return cls(
            use_id=str(data["use_id"]),
            certificate_id=str(data["certificate_id"]),
            target_id=str(data["target_id"]),
            judgment_kind=JudgmentKind(data["judgment_kind"]),
            use_kind=CertificateUseKind(data["use_kind"]),
            target_node=str(data["target_node"]),
            event_id=str(data.get("event_id", "event-0")),
            supports=tuple(str(item) for item in data.get("supports", ())),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class CertificateState(JsonModel):
    state_id: str
    certificate_id: str
    target_id: str
    state: CertificateStateValue
    target_node: str
    reason: str = ""
    checked_at: datetime = field(default_factory=utc_now)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CertificateState:
        return cls(
            state_id=str(data["state_id"]),
            certificate_id=str(data["certificate_id"]),
            target_id=str(data["target_id"]),
            state=CertificateStateValue(data["state"]),
            target_node=str(data["target_node"]),
            reason=str(data.get("reason", "")),
            checked_at=parse_datetime(data.get("checked_at")),
        )


@dataclass(frozen=True)
class CertificateRegistry(JsonModel):
    certificates: tuple[Certificate, ...] = ()
    targets: tuple[CertificateTarget, ...] = ()
    required: tuple[RequiredCertificate, ...] = ()
    uses: tuple[CertificateUse, ...] = ()
    states: tuple[CertificateState, ...] = ()

    def validate(
        self,
        *,
        support_graph: SupportGraph | None = None,
        now: datetime | None = None,
        include_transition_targets: bool = False,
    ) -> tuple[Problem, ...]:
        problems: list[Problem] = []
        certificates = {item.certificate_id: item for item in self.certificates}
        targets = {item.target_id: item for item in self.targets}
        states = {(item.certificate_id, item.target_id): item for item in self.states}
        uses_by_target: dict[str, list[CertificateUse]] = {}
        for use in self.uses:
            uses_by_target.setdefault(use.target_id, []).append(use)

        for use in self.uses:
            if use.target_id not in targets:
                problems.append(
                    Problem(
                        code="certificate.missing_target",
                        message=f"certificate use {use.use_id!r} has no registered target",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(use.use_id, use.target_id),
                    )
                )
                continue
            target = targets[use.target_id]
            if target.judgment_kind == JudgmentKind.TRANSITION and not include_transition_targets:
                continue
            if target.target_state != TargetState.COMPLETE:
                problems.append(
                    Problem(
                        code="certificate.target_state_not_complete",
                        message="registered certificate target state is not complete",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(target.target_id, target.target_node),
                    )
                )
            if use.certificate_id not in certificates:
                problems.append(
                    Problem(
                        code="certificate.unknown_certificate",
                        message=f"certificate {use.certificate_id!r} is not in the context",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(use.use_id, use.certificate_id),
                    )
                )
                continue
            cert = certificates[use.certificate_id]
            state = states.get((use.certificate_id, use.target_id))
            problems.extend(_validate_use(cert, target, use, state, support_graph, now))

        for required in self.required:
            req_target = targets.get(required.target_id)
            if req_target is None:
                problems.append(
                    Problem(
                        code="certificate.required_missing_target",
                        message=f"required certificate target {required.target_id!r} is absent",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(required.target_id, required.certificate_id),
                    )
                )
                continue
            if (
                req_target.judgment_kind == JudgmentKind.TRANSITION
                and not include_transition_targets
            ):
                continue
            matching = [
                use
                for use in uses_by_target.get(required.target_id, [])
                if use.certificate_id == required.certificate_id
            ]
            if required.required and not matching:
                problems.append(
                    Problem(
                        code="certificate.missing_required_use",
                        message="required certificate target has no target-indexed use",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(required.target_id, required.certificate_id),
                        suggested_repair=(
                            "Add a CertificateUse for the target or a checked "
                            "waiver/transfer/recheck disposition."
                        ),
                    )
                )

        for target in self.targets:
            if (
                target.judgment_kind != JudgmentKind.TRANSITION or include_transition_targets
            ) and target.target_state != TargetState.COMPLETE:
                problems.append(
                    Problem(
                        code="certificate.target_state_not_complete",
                        message="certificate target cannot pass with non-complete target state",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(target.target_id, target.target_node),
                    )
                )
            if target.required and target.target_id not in uses_by_target:
                problems.append(
                    Problem(
                        code="certificate.empty_required_target",
                        message=f"required target {target.target_id!r} has no certificate use",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(target.target_id, target.target_node),
                    )
                )

        return tuple(problems)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CertificateRegistry:
        return cls(
            certificates=tuple(
                Certificate.from_dict(item)
                for item in data.get("certificates", ())
                if isinstance(item, dict)
            ),
            targets=tuple(
                CertificateTarget.from_dict(item)
                for item in data.get("targets", ())
                if isinstance(item, dict)
            ),
            required=tuple(
                RequiredCertificate.from_dict(item)
                for item in data.get("required", ())
                if isinstance(item, dict)
            ),
            uses=tuple(
                CertificateUse.from_dict(item)
                for item in data.get("uses", ())
                if isinstance(item, dict)
            ),
            states=tuple(
                CertificateState.from_dict(item)
                for item in data.get("states", ())
                if isinstance(item, dict)
            ),
        )


def _validate_use(
    certificate: Certificate,
    target: CertificateTarget,
    use: CertificateUse,
    state: CertificateState | None,
    support_graph: SupportGraph | None,
    now: datetime | None,
) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    related = (use.use_id, certificate.certificate_id, target.target_id, target.target_node)
    if use.judgment_kind != target.judgment_kind or use.use_kind != target.use_kind:
        problems.append(
            Problem(
                code="certificate.target_mismatch",
                message="certificate use judgment or use kind does not match its target",
                severity=ProblemSeverity.ERROR,
                related_record_ids=related,
            )
        )
    if use.target_node != target.target_node:
        problems.append(
            Problem(
                code="certificate.target_node_mismatch",
                message="certificate use points at a different target node",
                severity=ProblemSeverity.ERROR,
                related_record_ids=related,
            )
        )
    if certificate.is_expired(now):
        problems.append(
            Problem(
                code="certificate.expired",
                message="used certificate is expired for its target",
                severity=ProblemSeverity.ERROR,
                related_record_ids=related,
            )
        )
    if certificate.metadata.get("revoked", False):
        problems.append(
            Problem(
                code="certificate.revoked",
                message="used certificate is revoked for its target",
                severity=ProblemSeverity.ERROR,
                related_record_ids=related,
            )
        )
    if certificate.metadata.get("issuer_conflict", False):
        problems.append(
            Problem(
                code="certificate.issuer_conflict",
                message="used certificate has an issuer conflict for its target",
                severity=ProblemSeverity.ERROR,
                related_record_ids=related,
            )
        )
    if certificate.metadata.get("monitor_expired", False):
        problems.append(
            Problem(
                code="certificate.monitor_expired",
                message="used certificate monitor is expired for its target",
                severity=ProblemSeverity.ERROR,
                related_record_ids=related,
            )
        )
    if certificate.metadata.get("kernel_mismatch", False):
        problems.append(
            Problem(
                code="certificate.kernel_mismatch",
                message="used certificate kernel requirements do not match this target",
                severity=ProblemSeverity.ERROR,
                related_record_ids=related,
            )
        )
    if not scope_covers(certificate.scope, target.scope):
        problems.append(
            Problem(
                code="certificate.scope_fail",
                message="certificate scope does not cover the registered target scope",
                severity=ProblemSeverity.ERROR,
                related_record_ids=related,
            )
        )
    if state is None:
        problems.append(
            Problem(
                code="certificate.missing_state",
                message="certificate use has no separate certificate-state node",
                severity=ProblemSeverity.ERROR,
                related_record_ids=related,
            )
        )
    else:
        if state.state_id == target.target_node:
            problems.append(
                Problem(
                    code="certificate.state_self_support",
                    message="certificate-state node must be separate from the target node",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(state.state_id, target.target_node),
                )
            )
        if state.state != CertificateStateValue.OK:
            problems.append(
                Problem(
                    code="certificate.state_not_ok",
                    message=f"certificate state is {state.state.value!r}, not ok",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(state.state_id, target.target_node),
                )
            )
    if support_graph is not None and state is not None:
        role = CERTIFICATE_USE_TO_SUPPORT_ROLE[target.use_kind]
        if not any(
            edge.source_id == state.state_id
            and edge.target_id == target.target_node
            and edge.role == role
            for edge in support_graph.edges
        ):
            problems.append(
                Problem(
                    code="certificate.missing_support_edge",
                    message="certificate-state node has no role-compatible support edge to target",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(state.state_id, target.target_node),
                )
            )
    return tuple(problems)


def scope_covers(certificate_scope: JsonDict, target_scope: JsonDict) -> bool:
    """Return whether finite certificate scope covers finite target scope."""

    for key, target_value in target_scope.items():
        if key not in certificate_scope:
            return False
        cert_value = certificate_scope[key]
        if cert_value == "*":
            continue
        if isinstance(cert_value, list):
            if isinstance(target_value, list):
                if not all(item in cert_value for item in target_value):
                    return False
            elif target_value not in cert_value:
                return False
        elif isinstance(target_value, dict):
            if not isinstance(cert_value, dict) or not scope_covers(cert_value, target_value):
                return False
        elif cert_value != target_value:
            return False
    return True
