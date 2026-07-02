from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from .certificates import Certificate, CertificateState, CertificateTarget, CertificateUse
from .enums import (
    CERTIFICATE_USE_TO_SUPPORT_ROLE,
    AnchorKind,
    CertificateStateValue,
    CertificateUseKind,
    EnvironmentTokenKind,
    EvidenceDisposition,
    EvidenceState,
    ImpactLevel,
    IssueSeverity,
    JudgmentKind,
    KernelAdmissionBasisKind,
    KernelAdmissionKind,
    KernelAdmissionStatus,
    LedgerStage,
    ObligationLifecycle,
    PhaseLevel,
    RecordType,
    SupportRole,
    TokenState,
)
from .environment import EnvironmentToken
from .ids import new_id
from .issues import Issue
from .ledger import EvaluatedLedger
from .model import LedgerRecord, SupportEdge, to_plain
from .modes import ModeContract
from .obligations import Obligation
from .stages import StageBuildRecord, ValidationCoordinate


@dataclass
class LedgerBuilder:
    """Convenience builder for practical AI-agent ledger records."""

    agent_id: str
    mode: str = "draft"

    def __post_init__(self) -> None:
        self._ledger = EvaluatedLedger(agent_id=self.agent_id, mode=self.mode)

    @property
    def ledger(self) -> EvaluatedLedger:
        return self._ledger

    def add_claim(
        self,
        text: str,
        *,
        event_id: str = "event-0",
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.CLAIM,
            LedgerStage.CANDIDATE,
            {"text": text},
            id=new_id("claim"),
            event_id=event_id,
            source=source or self.agent_id,
            metadata=metadata,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_evidence(
        self,
        text: str,
        *,
        supports: list[str] | tuple[str, ...] = (),
        event_id: str = "event-0",
        role: SupportRole | str = SupportRole.DATA,
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.EVIDENCE,
            LedgerStage.SUPPORT,
            {"text": text},
            id=new_id("evidence"),
            event_id=event_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record).mark_anchor(record.id)
        self._add_edges(record, supports, role=SupportRole(role), event_id=event_id)
        return record

    def add_support(
        self,
        text: str,
        *,
        supports: list[str] | tuple[str, ...],
        event_id: str = "event-0",
        role: SupportRole | str = SupportRole.DATA,
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.SUPPORT,
            LedgerStage.SUPPORT,
            {"text": text},
            id=new_id("support"),
            event_id=event_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record).mark_anchor(record.id)
        self._add_edges(record, supports, role=SupportRole(role), event_id=event_id)
        return record

    def add_process_class(
        self,
        *,
        process_id: str | None = None,
        class_name: str = "agent_process",
        modes: list[str] | tuple[str, ...] = ("*",),
        capabilities: list[str] | tuple[str, ...] = (),
        challenge_roles: list[str] | tuple[str, ...] = (),
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.PROCESS_CLASS,
            LedgerStage.CANDIDATE,
            {
                "process_id": process_id or self.agent_id,
                "class_name": class_name,
                "modes": tuple(modes),
                "capabilities": tuple(capabilities),
                "challenge_roles": tuple(challenge_roles),
                "reason": reason,
            },
            id=process_id or self.agent_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_distinction_basis(
        self,
        *,
        basis_id: str,
        distinctions: list[str] | tuple[str, ...],
        record_ids: list[str] | tuple[str, ...] = (),
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.DISTINCTION_BASIS,
            LedgerStage.CANDIDATE,
            {
                "basis_id": basis_id,
                "distinctions": tuple(distinctions),
                "record_ids": tuple(record_ids),
                "reason": reason,
            },
            id=basis_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_presentation(
        self,
        *,
        presentation_id: str,
        basis_id: str,
        expression_id: str | None = None,
        distinction_ids: list[str] | tuple[str, ...] = (),
        record_ids: list[str] | tuple[str, ...] = (),
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.FINITE_PRESENTATION,
            LedgerStage.CANDIDATE,
            {
                "presentation_id": presentation_id,
                "basis_id": basis_id,
                "expression_id": expression_id,
                "distinction_ids": tuple(distinction_ids),
                "record_ids": tuple(record_ids),
                "reason": reason,
            },
            id=presentation_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_finite_expression(
        self,
        *,
        expression_id: str,
        text: str,
        presentation_id: str | None = None,
        distinction_refs: list[str] | tuple[str, ...] = (),
        record_refs: list[str] | tuple[str, ...] = (),
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.FINITE_EXPRESSION,
            LedgerStage.CANDIDATE,
            {
                "expression_id": expression_id,
                "text": text,
                "presentation_id": presentation_id,
                "distinction_refs": tuple(distinction_refs),
                "record_refs": tuple(record_refs),
                "reason": reason,
            },
            id=expression_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_presentation_map(
        self,
        *,
        map_id: str,
        presentation_id: str,
        domain_distinctions: list[str] | tuple[str, ...] = (),
        mapped_distinctions: list[str] | tuple[str, ...] = (),
        target_records: list[str] | tuple[str, ...] = (),
        total: bool = True,
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.PRESENTATION_MAP,
            LedgerStage.CHECKED_CORE,
            {
                "map_id": map_id,
                "presentation_id": presentation_id,
                "domain_distinctions": tuple(domain_distinctions),
                "mapped_distinctions": tuple(mapped_distinctions),
                "target_records": tuple(target_records),
                "total": total,
                "reason": reason,
            },
            id=map_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_issue(
        self,
        text: str,
        *,
        severity: IssueSeverity | str = IssueSeverity.MEDIUM,
        blocking: bool = False,
        resolved: bool = False,
    ) -> LedgerRecord:
        issue = Issue.create(text, severity=severity, blocking=blocking, resolved=resolved)
        record = LedgerRecord.create(
            RecordType.ISSUE,
            LedgerStage.CHECKED_CORE,
            issue.to_dict(),
            id=issue.issue_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_requirement(
        self,
        requirement_id: str,
        text: str,
        *,
        reason: str = "",
        empty_requirement_reason: str | None = None,
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.REQUIREMENT,
            LedgerStage.CHECKED_CORE,
            {
                "text": text,
                "reason": reason,
                "empty_requirement_reason": empty_requirement_reason,
            },
            id=requirement_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_requirement_policy(
        self,
        *,
        policy_id: str,
        process_id: str = "",
        requirements: list[str] | tuple[str, ...] = (),
        issue_ids: list[str] | tuple[str, ...] = (),
        empty: bool = False,
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.REQUIREMENT_POLICY,
            LedgerStage.CHECKED_CORE,
            {
                "policy_id": policy_id,
                "process_id": process_id,
                "mode": self.mode,
                "requirements": tuple(requirements),
                "issue_ids": tuple(issue_ids),
                "empty": empty,
                "reason": reason,
            },
            id=policy_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_requirement_reason(
        self,
        *,
        requirement_id: str,
        source_policy_id: str = "",
        reason: str,
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.REQUIREMENT_REASON,
            LedgerStage.CHECKED_CORE,
            {
                "requirement_id": requirement_id,
                "source_policy_id": source_policy_id,
                "reason": reason,
            },
            id=new_id("req-reason"),
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_requirement_transfer(
        self,
        *,
        requirement_id: str,
        from_mode: str,
        to_mode: str,
        accepted: bool = True,
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.REQUIREMENT_TRANSFER,
            LedgerStage.CHECKED_CORE,
            {
                "requirement_id": requirement_id,
                "from_mode": from_mode,
                "to_mode": to_mode,
                "accepted": accepted,
                "reason": reason,
            },
            id=new_id("req-transfer"),
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_obligation(
        self,
        text: str,
        *,
        lifecycle: ObligationLifecycle | str = ObligationLifecycle.DECLARED,
        hard: bool = False,
        owner: str | None = None,
        due_at: datetime | None = None,
        support_refs: list[str] | tuple[str, ...] = (),
    ) -> LedgerRecord:
        obligation = Obligation.create(
            text,
            lifecycle=lifecycle,
            hard=hard,
            owner=owner,
            due_at=due_at,
            support_refs=tuple(support_refs),
        )
        record = LedgerRecord.create(
            RecordType.OBLIGATION,
            LedgerStage.CHECKED_POLICY,
            obligation.to_dict(),
            id=obligation.obligation_id,
            source=self.agent_id,
            support_refs=tuple(support_refs),
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_obligation_lifecycle(
        self,
        obligation_id: str,
        *,
        source: ObligationLifecycle | str,
        target: ObligationLifecycle | str,
        event_id: str = "event-0",
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.OBLIGATION_LIFECYCLE,
            LedgerStage.CHECKED_POLICY,
            {
                "obligation_id": obligation_id,
                "source": ObligationLifecycle(source).value,
                "target": ObligationLifecycle(target).value,
                "event_id": event_id,
                "reason": reason,
            },
            id=new_id("obl-life"),
            event_id=event_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_environment_token(
        self,
        *,
        kind: EnvironmentTokenKind | str,
        name: str,
        state: TokenState | str = TokenState.OK,
        selected: bool = True,
        known_relevant: bool = False,
        reason: str = "",
    ) -> LedgerRecord:
        token = EnvironmentToken.create(
            kind=kind,
            name=name,
            state=state,
            selected=selected,
            known_relevant=known_relevant,
            reason=reason,
        )
        record = LedgerRecord.create(
            RecordType.ENVIRONMENT_TOKEN,
            LedgerStage.CHECKED_POLICY,
            token.to_dict(),
            id=token.token_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_critic_coverage(
        self,
        *,
        role: str = "external_challenge",
        covered: bool = True,
        waived: bool = False,
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.CRITIC_COVERAGE,
            LedgerStage.CHECKED_POLICY,
            {"role": role, "covered": covered, "waived": waived, "reason": reason},
            id=new_id("critic"),
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_failure(
        self,
        text: str,
        *,
        mode: str | None = None,
        relevant: bool = True,
        blocking: bool = True,
        resolved: bool = False,
        severity: IssueSeverity | str = IssueSeverity.HIGH,
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.FAILURE,
            LedgerStage.CHECKED_POLICY,
            {
                "text": text,
                "failure_id": new_id("failure"),
                "mode": mode or self.mode,
                "relevant": relevant,
                "blocking": blocking,
                "resolved": resolved,
                "severity": IssueSeverity(severity).value,
            },
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_acceptance(
        self,
        target_id: str,
        *,
        accepted: bool,
        accepted_by: list[str] | tuple[str, ...] = (),
        blocked_by: list[str] | tuple[str, ...] = (),
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.ACCEPTANCE,
            LedgerStage.CHECKED_POLICY,
            {
                "target_id": target_id,
                "accepted": accepted,
                "accepted_by": tuple(accepted_by),
                "blocked_by": tuple(blocked_by),
                "reason": reason,
            },
            id=new_id("accept"),
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_abstention(
        self,
        target_id: str,
        *,
        obstructed: bool = False,
        obstruction_refs: list[str] | tuple[str, ...] = (),
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.ABSTENTION,
            LedgerStage.CHECKED_POLICY,
            {
                "target_id": target_id,
                "abstained": True,
                "obstructed": obstructed,
                "obstruction_refs": tuple(obstruction_refs),
                "reason": reason,
            },
            id=new_id("abstain"),
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_validator_timeout(
        self,
        validator_id: str,
        *,
        timeout_ms: int,
        hidden: bool = False,
        blocks: bool = True,
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.VALIDATOR_TIMEOUT,
            LedgerStage.CHECKED_POLICY,
            {
                "validator_id": validator_id,
                "timeout_ms": timeout_ms,
                "hidden": hidden,
                "blocks": blocks,
                "reason": reason,
            },
            id=new_id("timeout"),
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_consistency_profile(
        self,
        profile_id: str,
        *,
        passed: bool = True,
        missing_coordinates: list[str] | tuple[str, ...] = (),
        failed_coordinates: list[str] | tuple[str, ...] = (),
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.CONSISTENCY_PROFILE,
            LedgerStage.CHECKED_POLICY,
            {
                "profile_id": profile_id,
                "passed": passed,
                "missing_coordinates": tuple(missing_coordinates),
                "failed_coordinates": tuple(failed_coordinates),
                "reason": reason,
            },
            id=profile_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_settledness_declaration(
        self,
        *,
        distinction_id: str,
        presentation_id: str = "",
        declared_by: str = "",
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.SETTLEDNESS_DECLARATION,
            LedgerStage.CHECKED_CORE,
            {
                "distinction_id": distinction_id,
                "presentation_id": presentation_id,
                "declared_by": declared_by or self.agent_id,
                "reason": reason,
            },
            id=new_id("settled-decl"),
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_settledness_license(
        self,
        *,
        distinction_id: str,
        license_id: str | None = None,
        presentation_id: str = "",
        licensed: bool = True,
        checker_record_id: str = "",
        support_refs: list[str] | tuple[str, ...] = (),
        reason: str = "",
    ) -> LedgerRecord:
        record_id = license_id or new_id("settled-license")
        record = LedgerRecord.create(
            RecordType.SETTLEDNESS_LICENSE,
            LedgerStage.CHECKED_CORE,
            {
                "license_id": record_id,
                "distinction_id": distinction_id,
                "presentation_id": presentation_id,
                "licensed": licensed,
                "checker_record_id": checker_record_id,
                "support_refs": tuple(support_refs),
                "reason": reason,
            },
            id=record_id,
            source=self.agent_id,
            support_refs=tuple(support_refs),
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_obstruction_profile(
        self,
        *,
        profile_id: str,
        obstruction_ids: list[str] | tuple[str, ...] = (),
        critical_obstructions: list[str] | tuple[str, ...] = (),
        discharged_obstructions: list[str] | tuple[str, ...] = (),
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.OBSTRUCTION_PROFILE,
            LedgerStage.CHECKED_CORE,
            {
                "profile_id": profile_id,
                "obstruction_ids": tuple(obstruction_ids),
                "critical_obstructions": tuple(critical_obstructions),
                "discharged_obstructions": tuple(discharged_obstructions),
                "reason": reason,
            },
            id=profile_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_null_certificate(
        self,
        *,
        certificate_id: str,
        target_id: str,
        allowed: bool = False,
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.NULL_CERTIFICATE,
            LedgerStage.CHECKED_POLICY,
            {
                "certificate_id": certificate_id,
                "target_id": target_id,
                "allowed": allowed,
                "reason": reason,
            },
            id=certificate_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_certificate_cover(
        self,
        *,
        cover_id: str,
        obstruction_id: str,
        certificate_id: str,
        target_id: str,
        discharged: bool = False,
        support_refs: list[str] | tuple[str, ...] = (),
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.CERTIFICATE_COVER,
            LedgerStage.CHECKED_POLICY,
            {
                "cover_id": cover_id,
                "obstruction_id": obstruction_id,
                "certificate_id": certificate_id,
                "target_id": target_id,
                "discharged": discharged,
                "support_refs": tuple(support_refs),
                "reason": reason,
            },
            id=cover_id,
            source=self.agent_id,
            support_refs=tuple(support_refs),
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_obligation_discharge(
        self,
        *,
        discharge_id: str,
        obligation_id: str,
        obstruction_id: str = "",
        certificate_cover_id: str = "",
        discharged: bool = True,
        support_refs: list[str] | tuple[str, ...] = (),
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.OBLIGATION_DISCHARGE,
            LedgerStage.CHECKED_POLICY,
            {
                "discharge_id": discharge_id,
                "obligation_id": obligation_id,
                "obstruction_id": obstruction_id,
                "certificate_cover_id": certificate_cover_id,
                "discharged": discharged,
                "support_refs": tuple(support_refs),
                "reason": reason,
            },
            id=discharge_id,
            source=self.agent_id,
            support_refs=tuple(support_refs),
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_respect_certificate(
        self,
        *,
        respect_id: str,
        subject_record_id: str,
        required_coordinates: list[str] | tuple[str, ...],
        respected_coordinates: list[str] | tuple[str, ...],
        valid: bool = True,
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.RESPECT_CERTIFICATE,
            LedgerStage.CHECKED_POLICY,
            {
                "respect_id": respect_id,
                "subject_record_id": subject_record_id,
                "required_coordinates": tuple(required_coordinates),
                "respected_coordinates": tuple(respected_coordinates),
                "valid": valid,
                "reason": reason,
            },
            id=respect_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_impact(self, impact: ImpactLevel | str, *, reason: str = "") -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.IMPACT_RECORD,
            LedgerStage.CHECKED_POLICY,
            {"impact": ImpactLevel(impact).value, "reason": reason},
            id=new_id("impact"),
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_certificate(
        self,
        *,
        issuer: str,
        scope: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
        certificate_id: str | None = None,
    ) -> LedgerRecord:
        cert = Certificate(
            certificate_id=certificate_id or new_id("cert"),
            issuer=issuer,
            scope=to_plain(scope or {}),  # type: ignore[arg-type]
            expires_at=expires_at,
        )
        record = LedgerRecord.create(
            RecordType.CERTIFICATE,
            LedgerStage.CANDIDATE,
            cert.to_dict(),
            id=cert.certificate_id,
            source=issuer,
        )
        self._ledger = self._ledger.add_record(record).mark_anchor(record.id)
        return record

    def add_certificate_target(
        self,
        *,
        target_node: str,
        judgment_kind: JudgmentKind | str,
        use_kind: CertificateUseKind | str,
        target_id: str | None = None,
        scope: dict[str, Any] | None = None,
        required: bool = False,
        event_id: str = "event-0",
    ) -> LedgerRecord:
        target = CertificateTarget(
            target_id=target_id or new_id("target"),
            judgment_kind=JudgmentKind(judgment_kind),
            use_kind=CertificateUseKind(use_kind),
            target_node=target_node,
            event_id=event_id,
            scope=to_plain(scope or {}),  # type: ignore[arg-type]
            required=required,
        )
        record = LedgerRecord.create(
            RecordType.CERTIFICATE_TARGET,
            LedgerStage.CHECKED_POLICY,
            target.to_dict(),
            id=target.target_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_certificate_use(
        self,
        *,
        certificate_id: str,
        target_id: str,
        target_node: str,
        judgment_kind: JudgmentKind | str,
        use_kind: CertificateUseKind | str,
        state: CertificateStateValue | str = CertificateStateValue.OK,
        event_id: str = "event-0",
    ) -> tuple[LedgerRecord, LedgerRecord]:
        use = CertificateUse.create(
            certificate_id=certificate_id,
            target_id=target_id,
            judgment_kind=judgment_kind,
            use_kind=use_kind,
            target_node=target_node,
            event_id=event_id,
        )
        state_model = CertificateState(
            state_id=new_id("cert-state"),
            certificate_id=certificate_id,
            target_id=target_id,
            state=CertificateStateValue(state),
            target_node=target_node,
        )
        use_record = LedgerRecord.create(
            RecordType.CERTIFICATE_USE,
            LedgerStage.CHECKED_POLICY,
            {**use.to_dict(), "state": CertificateStateValue(state).value},
            id=use.use_id,
            source=self.agent_id,
        )
        state_record = LedgerRecord.create(
            RecordType.CERTIFICATE_STATE,
            LedgerStage.CHECKED_POLICY,
            state_model.to_dict(),
            id=state_model.state_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_records((use_record, state_record))
        role = CERTIFICATE_USE_TO_SUPPORT_ROLE[CertificateUseKind(use_kind)]
        self._ledger = self._ledger.add_support_edge(
            SupportEdge(
                source_id=state_record.id,
                target_id=target_node,
                role=role,
                reason="target-indexed certificate state supports target",
                event_id=event_id,
                witness_id=use_record.id,
            )
        )
        return use_record, state_record

    def add_scope_exclusion(self, item: str, *, disposition: str, reason: str = "") -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.SCOPE_EXCLUSION,
            LedgerStage.CHECKED_POLICY,
            {"item": item, "disposition": disposition, "reason": reason},
            id=new_id("scope"),
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_mode_closure(self, *, state: str = "pass", reason: str = "") -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.MODE_CLOSURE,
            LedgerStage.CHECKED_POLICY,
            {"state": state, "reason": reason},
            id=new_id("modeclosure"),
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_compression_use(self, *, sufficient: bool, reason: str = "") -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.COMPRESSION_USE,
            LedgerStage.CHECKED_POLICY,
            {"sufficient": sufficient, "reason": reason},
            id=new_id("compression"),
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_compression_profile_class(
        self,
        *,
        profile_class_id: str,
        profiles: list[str] | tuple[str, ...],
        admissibility_by_profile: dict[str, Any],
        compressed_values: dict[str, Any],
        mode: str | None = None,
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.COMPRESSION_PROFILE_CLASS,
            LedgerStage.CHECKED_POLICY,
            {
                "profile_class_id": profile_class_id,
                "profiles": tuple(profiles),
                "admissibility_by_profile": to_plain(admissibility_by_profile),
                "compressed_values": to_plain(compressed_values),
                "mode": mode or self.mode,
                "reason": reason,
            },
            id=profile_class_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_compression_factorization(
        self,
        *,
        factorization_id: str,
        profile_class_id: str,
        beta_by_value: dict[str, Any],
        valid: bool = True,
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.COMPRESSION_FACTORIZATION,
            LedgerStage.CHECKED_POLICY,
            {
                "factorization_id": factorization_id,
                "profile_class_id": profile_class_id,
                "beta_by_value": to_plain(beta_by_value),
                "valid": valid,
                "reason": reason,
            },
            id=factorization_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_record_preserving_refinement(
        self,
        *,
        transition_id: str,
        before_record_ids: list[str] | tuple[str, ...],
        preserved_record_ids: list[str] | tuple[str, ...] = (),
        archived_record_ids: list[str] | tuple[str, ...] = (),
        provenance_edge_ids: list[str] | tuple[str, ...] = (),
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.RECORD_PRESERVING_REFINEMENT,
            LedgerStage.TRANSITION,
            {
                "transition_id": transition_id,
                "before_record_ids": tuple(before_record_ids),
                "preserved_record_ids": tuple(preserved_record_ids),
                "archived_record_ids": tuple(archived_record_ids),
                "provenance_edge_ids": tuple(provenance_edge_ids),
                "reason": reason,
            },
            id=transition_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_self_modification_witness(
        self,
        *,
        witness_id: str,
        previous_process_id: str,
        next_process_id: str,
        lineage_record_id: str | None = None,
        lineage_reason: str = "",
        checker_version: str = "",
        rule_version: str = "",
        kernel_update_record_id: str | None = None,
        preserved_checks: list[str] | tuple[str, ...] = (),
        replaced_checks: list[str] | tuple[str, ...] = (),
        unavailable_checks: list[str] | tuple[str, ...] = (),
        reason: str = "",
    ) -> LedgerRecord:
        record = LedgerRecord.create(
            RecordType.SELF_MODIFICATION_WITNESS,
            LedgerStage.TRANSITION,
            {
                "witness_id": witness_id,
                "previous_process_id": previous_process_id,
                "next_process_id": next_process_id,
                "lineage_record_id": lineage_record_id,
                "lineage_reason": lineage_reason,
                "checker_version": checker_version,
                "rule_version": rule_version,
                "kernel_update_record_id": kernel_update_record_id,
                "preserved_checks": tuple(preserved_checks),
                "replaced_checks": tuple(replaced_checks),
                "unavailable_checks": tuple(unavailable_checks),
                "reason": reason,
            },
            id=witness_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_anchor_declaration(
        self,
        *,
        anchor_id: str,
        anchor_kind: AnchorKind | str = AnchorKind.DECLARED_SUPPORT,
        target_id: str | None = None,
        event_id: str = "event-0",
        event_free: bool = False,
        provenance_ref: str | None = None,
        root_debt_id: str | None = None,
        permitted_roles: list[str] | tuple[str, ...] = (),
        reason: str = "",
    ) -> LedgerRecord:
        declaration_id = new_id("anchor_decl")
        record = LedgerRecord.create(
            RecordType.ANCHOR_DECLARATION,
            LedgerStage.CHECKED_CORE,
            {
                "anchor_id": anchor_id,
                "target_id": target_id or anchor_id,
                "anchor_kind": AnchorKind(anchor_kind),
                "event_id": event_id,
                "event_free": event_free,
                "provenance_ref": provenance_ref,
                "root_debt_id": root_debt_id,
                "permitted_roles": tuple(permitted_roles),
                "reason": reason,
            },
            id=declaration_id,
            event_id=event_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_adequacy_record(
        self,
        *,
        component: str,
        state: EvidenceState | str = EvidenceState.PASS,
        disposition: EvidenceDisposition | str = EvidenceDisposition.ACCEPTED,
        adequacy_id: str | None = None,
        input_record_ids: list[str] | tuple[str, ...] = (),
        issue_ids: list[str] | tuple[str, ...] = (),
        obligation_ids: list[str] | tuple[str, ...] = (),
        support_refs: list[str] | tuple[str, ...] = (),
        checker_version_id: str = "checker-v1",
        rule_version_id: str = "rules-v1",
        mode: str | None = None,
        waived: bool = False,
        reason: str = "",
    ) -> LedgerRecord:
        record_id = adequacy_id or new_id("adequacy")
        record = LedgerRecord.create(
            RecordType.ADEQUACY_RECORD,
            LedgerStage.CHECKED_POLICY,
            {
                "adequacy_id": record_id,
                "component": component,
                "state": EvidenceState(state),
                "disposition": EvidenceDisposition(disposition),
                "input_record_ids": tuple(input_record_ids),
                "issue_ids": tuple(issue_ids),
                "obligation_ids": tuple(obligation_ids),
                "support_refs": tuple(support_refs),
                "checker_version_id": checker_version_id,
                "rule_version_id": rule_version_id,
                "mode": mode or self.mode,
                "waived": waived,
                "reason": reason,
            },
            id=record_id,
            source=self.agent_id,
            support_refs=tuple(support_refs),
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_kernel_admission(
        self,
        *,
        version_id: str,
        checker_version_id: str,
        admission_id: str | None = None,
        kind: KernelAdmissionKind | str = KernelAdmissionKind.RULE,
        status: KernelAdmissionStatus | str = KernelAdmissionStatus.ADMITTED,
        basis_kind: KernelAdmissionBasisKind | str = KernelAdmissionBasisKind.ROOT,
        basis_id: str | None = None,
        root_debt_id: str | None = None,
        reason: str = "",
    ) -> LedgerRecord:
        record_id = admission_id or new_id("kernel_admission")
        record = LedgerRecord.create(
            RecordType.KERNEL_ADMISSION,
            LedgerStage.CHECKED_CORE,
            {
                "admission_id": record_id,
                "version_id": version_id,
                "kind": KernelAdmissionKind(kind),
                "status": KernelAdmissionStatus(status),
                "basis_kind": KernelAdmissionBasisKind(basis_kind),
                "checker_version_id": checker_version_id,
                "basis_id": basis_id,
                "root_debt_id": root_debt_id,
                "reason": reason,
            },
            id=record_id,
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        return record

    def add_status_body(
        self,
        *,
        target_id: str,
        body_id: str | None = None,
        support_coordinates: list[str] | tuple[str, ...] = (),
        read_coordinates: list[str] | tuple[str, ...] = (),
        respect_coordinates: list[str] | tuple[str, ...] = (),
        support_refs: list[str] | tuple[str, ...] = (),
        checker_version_id: str = "checker-v1",
        rule_version_id: str = "rules-v1",
        reads_final_output: bool = False,
        reason: str = "",
    ) -> LedgerRecord:
        record_id = body_id or new_id("status_body")
        record = LedgerRecord.create(
            RecordType.STATUS_BODY,
            LedgerStage.CHECKED_STATUS,
            {
                "body_id": record_id,
                "target_id": target_id,
                "support_coordinates": tuple(support_coordinates),
                "read_coordinates": tuple(read_coordinates),
                "respect_coordinates": tuple(respect_coordinates),
                "checker_version_id": checker_version_id,
                "rule_version_id": rule_version_id,
                "reads_final_output": reads_final_output,
                "reason": reason,
            },
            id=record_id,
            source=self.agent_id,
            support_refs=tuple(support_refs),
            metadata={"target_id": target_id},
        )
        self._ledger = self._ledger.add_record(record)
        self._set_validation_coordinate(record, PhaseLevel.STATUS_BODY, target_id=target_id)
        for source_id in support_refs:
            self._ledger = self._ledger.add_support_edge(
                SupportEdge(
                    source_id=source_id,
                    target_id=record.id,
                    role=SupportRole.STATUS_BODY,
                    reason=reason,
                    witness_id=source_id,
                )
            )
        return record

    def add_checked_status(
        self,
        *,
        body_record_id: str,
        status: str = "supported",
        status_id: str | None = None,
        read_coordinates: list[str] | tuple[str, ...] = (),
        respect_coordinates: list[str] | tuple[str, ...] = (),
        support_refs: list[str] | tuple[str, ...] = (),
        checker_version_id: str = "checker-v1",
        rule_version_id: str = "rules-v1",
        checked: bool = True,
        reads_final_output: bool = False,
        reason: str = "",
    ) -> LedgerRecord:
        record_id = status_id or new_id("checked_status")
        refs = tuple(dict.fromkeys((body_record_id, *support_refs)))
        record = LedgerRecord.create(
            RecordType.CHECKED_STATUS,
            LedgerStage.CHECKED_STATUS,
            {
                "status_id": record_id,
                "body_record_id": body_record_id,
                "status": status,
                "checker_version_id": checker_version_id,
                "rule_version_id": rule_version_id,
                "read_coordinates": tuple(read_coordinates),
                "respect_coordinates": tuple(respect_coordinates),
                "checked": checked,
                "reads_final_output": reads_final_output,
                "reason": reason,
            },
            id=record_id,
            source=self.agent_id,
            support_refs=refs,
        )
        self._ledger = self._ledger.add_record(record).mark_checked(record.id)
        self._set_validation_coordinate(record, PhaseLevel.CHECKED_STATUS)
        self._ledger = self._ledger.add_support_edge(
            SupportEdge(
                source_id=body_record_id,
                target_id=record.id,
                role=SupportRole.STATUS_CHECK,
                reason=reason,
                witness_id=body_record_id,
            )
        )
        return record

    def add_pre_admissibility_support_vector(
        self,
        *,
        target_id: str,
        vector_id: str | None = None,
        support_coordinates: list[str] | tuple[str, ...] = (),
        validator_coordinates: list[str] | tuple[str, ...] = (),
        kernel_coordinates: list[str] | tuple[str, ...] = (),
        certificate_coordinates: list[str] | tuple[str, ...] = (),
        environment_coordinates: list[str] | tuple[str, ...] = (),
        obligation_coordinates: list[str] | tuple[str, ...] = (),
        adequacy_coordinates: list[str] | tuple[str, ...] = (),
        support_refs: list[str] | tuple[str, ...] = (),
        checker_version_id: str = "checker-v1",
        rule_version_id: str = "rules-v1",
        reason: str = "",
    ) -> LedgerRecord:
        record_id = vector_id or new_id("pre_admissibility")
        record = LedgerRecord.create(
            RecordType.PRE_ADMISSIBILITY_SUPPORT_VECTOR,
            LedgerStage.CHECKED_ADMISSIBILITY,
            {
                "vector_id": record_id,
                "target_id": target_id,
                "support_coordinates": tuple(support_coordinates),
                "validator_coordinates": tuple(validator_coordinates),
                "kernel_coordinates": tuple(kernel_coordinates),
                "certificate_coordinates": tuple(certificate_coordinates),
                "environment_coordinates": tuple(environment_coordinates),
                "obligation_coordinates": tuple(obligation_coordinates),
                "adequacy_coordinates": tuple(adequacy_coordinates),
                "checker_version_id": checker_version_id,
                "rule_version_id": rule_version_id,
                "reason": reason,
            },
            id=record_id,
            source=self.agent_id,
            metadata={"target_id": target_id},
        )
        self._ledger = self._ledger.add_record(record)
        self._set_validation_coordinate(record, PhaseLevel.ADMISSIBILITY_BODY, target_id=target_id)
        for source_id in support_refs:
            self._ledger = self._ledger.add_support_edge(
                SupportEdge(
                    source_id=source_id,
                    target_id=record.id,
                    role=SupportRole.ADMISSIBILITY_BODY,
                    reason=reason,
                    witness_id=source_id,
                )
            )
        return record

    def add_admissibility_body(
        self,
        *,
        target_id: str,
        body_id: str | None = None,
        status_body_record_id: str | None = None,
        pre_admissibility_vector_id: str | None = None,
        support_coordinates: list[str] | tuple[str, ...] = (),
        read_coordinates: list[str] | tuple[str, ...] = (),
        respect_coordinates: list[str] | tuple[str, ...] = (),
        support_refs: list[str] | tuple[str, ...] = (),
        checker_version_id: str = "checker-v1",
        rule_version_id: str = "rules-v1",
        reads_final_output: bool = False,
        reason: str = "",
    ) -> LedgerRecord:
        record_id = body_id or new_id("admissibility_body")
        record = LedgerRecord.create(
            RecordType.ADMISSIBILITY_BODY,
            LedgerStage.CHECKED_ADMISSIBILITY,
            {
                "body_id": record_id,
                "target_id": target_id,
                "status_body_record_id": status_body_record_id,
                "pre_admissibility_vector_id": pre_admissibility_vector_id,
                "support_coordinates": tuple(support_coordinates),
                "read_coordinates": tuple(read_coordinates),
                "respect_coordinates": tuple(respect_coordinates),
                "checker_version_id": checker_version_id,
                "rule_version_id": rule_version_id,
                "reads_final_output": reads_final_output,
                "reason": reason,
            },
            id=record_id,
            source=self.agent_id,
            support_refs=tuple(support_refs),
            metadata={"target_id": target_id},
        )
        self._ledger = self._ledger.add_record(record)
        self._set_validation_coordinate(record, PhaseLevel.ADMISSIBILITY_BODY, target_id=target_id)
        for source_id in support_refs:
            self._ledger = self._ledger.add_support_edge(
                SupportEdge(
                    source_id=source_id,
                    target_id=record.id,
                    role=SupportRole.ADMISSIBILITY_BODY,
                    reason=reason,
                    witness_id=source_id,
                )
            )
        return record

    def add_checked_admissibility(
        self,
        *,
        body_record_id: str,
        pre_admissibility_vector_id: str,
        admissibility: str = "admissible",
        admissibility_id: str | None = None,
        read_coordinates: list[str] | tuple[str, ...] = (),
        respect_coordinates: list[str] | tuple[str, ...] = (),
        support_refs: list[str] | tuple[str, ...] = (),
        checker_version_id: str = "checker-v1",
        rule_version_id: str = "rules-v1",
        checked: bool = True,
        reads_final_output: bool = False,
        reason: str = "",
    ) -> LedgerRecord:
        record_id = admissibility_id or new_id("checked_admissibility")
        refs = tuple(dict.fromkeys((body_record_id, pre_admissibility_vector_id, *support_refs)))
        record = LedgerRecord.create(
            RecordType.CHECKED_ADMISSIBILITY,
            LedgerStage.CHECKED_ADMISSIBILITY,
            {
                "admissibility_id": record_id,
                "body_record_id": body_record_id,
                "admissibility": admissibility,
                "checker_version_id": checker_version_id,
                "pre_admissibility_vector_id": pre_admissibility_vector_id,
                "rule_version_id": rule_version_id,
                "read_coordinates": tuple(read_coordinates),
                "respect_coordinates": tuple(respect_coordinates),
                "checked": checked,
                "reads_final_output": reads_final_output,
                "reason": reason,
            },
            id=record_id,
            source=self.agent_id,
            support_refs=refs,
        )
        self._ledger = self._ledger.add_record(record).mark_checked(record.id)
        self._set_validation_coordinate(record, PhaseLevel.CHECKED_ADMISSIBILITY)
        for source_id, role in (
            (body_record_id, SupportRole.ADMISSIBILITY_BODY),
            (pre_admissibility_vector_id, SupportRole.ADMISSIBILITY_CHECK),
        ):
            self._ledger = self._ledger.add_support_edge(
                SupportEdge(
                    source_id=source_id,
                    target_id=record.id,
                    role=role,
                    reason=reason,
                    witness_id=source_id,
                )
            )
        return record

    def finalize_checked(
        self,
        *,
        checker_version_id: str = "checker-v1",
        rule_version_id: str = "rules-v1",
    ) -> EvaluatedLedger:
        target = self._latest_target_record()
        if target is None:
            target = self.add_claim("No output claim was recorded before finalization.")
        support_ids = tuple(record.id for record in self._ledger.find(RecordType.SUPPORT))
        evidence_ids = tuple(record.id for record in self._ledger.find(RecordType.EVIDENCE))
        for anchor_id in self._ledger.support_graph.anchors:
            if not self._has_anchor_declaration(anchor_id):
                self.add_anchor_declaration(
                    anchor_id=anchor_id,
                    anchor_kind=AnchorKind.DECLARED_SUPPORT,
                    reason="Anchor made explicit for strict finality.",
                )
        root_debt = self._ensure_root_debt()
        self.add_kernel_admission(
            version_id=rule_version_id,
            checker_version_id=checker_version_id,
            basis_kind=KernelAdmissionBasisKind.ROOT,
            root_debt_id=root_debt.id,
            reason="Strict finality uses visible root-debt admission.",
        )
        self.add_kernel_admission(
            version_id=checker_version_id,
            checker_version_id=rule_version_id,
            kind=KernelAdmissionKind.CHECKER,
            basis_kind=KernelAdmissionBasisKind.PRIOR_KERNEL,
            basis_id=root_debt.id,
            reason="Checker version is admitted by a finite prior-kernel witness.",
        )
        contract = ModeContract.for_name(self.mode)
        for component in contract.adequacy_rules:
            if not self._has_adequacy_record(component):
                self.add_adequacy_record(
                    component=component,
                    state=EvidenceState.PASS,
                    disposition=EvidenceDisposition.ACCEPTED,
                    input_record_ids=(target.id, *support_ids, *evidence_ids),
                    checker_version_id=checker_version_id,
                    rule_version_id=rule_version_id,
                    reason="Persisted finite adequacy disposition for strict finality.",
                )
        status_body = self.add_status_body(
            target_id=target.id,
            support_coordinates=("support",),
            read_coordinates=contract.required_read_coordinates,
            respect_coordinates=contract.required_respect_coordinates,
            support_refs=(*support_ids, *evidence_ids),
            checker_version_id=checker_version_id,
            rule_version_id=rule_version_id,
            reason="Status body reads only pre-final finite coordinates.",
        )
        checked_status = self.add_checked_status(
            body_record_id=status_body.id,
            status="supported",
            read_coordinates=contract.required_read_coordinates,
            respect_coordinates=contract.required_respect_coordinates,
            checker_version_id=checker_version_id,
            rule_version_id=rule_version_id,
            reason="Checked status over a separate status body.",
        )
        vector = self.add_pre_admissibility_support_vector(
            target_id=target.id,
            support_coordinates=("support",),
            validator_coordinates=("payload", "support_graph", "stage"),
            kernel_coordinates=(rule_version_id, checker_version_id),
            certificate_coordinates=("certificates",),
            environment_coordinates=contract.environment_token_selection_rules,
            obligation_coordinates=("obligations",),
            adequacy_coordinates=contract.adequacy_rules,
            support_refs=(status_body.id,),
            checker_version_id=checker_version_id,
            rule_version_id=rule_version_id,
            reason="Pre-admissibility support vector excludes final checked outputs.",
        )
        admissibility_body = self.add_admissibility_body(
            target_id=target.id,
            status_body_record_id=status_body.id,
            pre_admissibility_vector_id=vector.id,
            support_coordinates=("support",),
            read_coordinates=contract.required_read_coordinates,
            respect_coordinates=contract.required_respect_coordinates,
            support_refs=(status_body.id,),
            checker_version_id=checker_version_id,
            rule_version_id=rule_version_id,
            reason="Admissibility body is separate from checked status.",
        )
        checked_admissibility = self.add_checked_admissibility(
            body_record_id=admissibility_body.id,
            pre_admissibility_vector_id=vector.id,
            admissibility="admissible",
            read_coordinates=contract.required_read_coordinates,
            respect_coordinates=contract.required_respect_coordinates,
            checker_version_id=checker_version_id,
            rule_version_id=rule_version_id,
            reason="Checked admissibility over finite pre-admissibility coordinates.",
        )
        self._ledger = self._ledger.add_stage_build(
            StageBuildRecord(
                build_id=new_id("stage_build"),
                input_stage=LedgerStage.CHECKED_POLICY,
                output_stage=LedgerStage.CHECKED_STATUS,
                phase_start=PhaseLevel.STATUS_BODY,
                phase_end=PhaseLevel.CHECKED_STATUS,
                rule_versions=(rule_version_id,),
                checker_versions=(checker_version_id,),
                input_frontier=(target.id, *support_ids, *evidence_ids),
                emitted_records=(status_body.id, checked_status.id),
                reads=(target.id, *support_ids, *evidence_ids),
                reason="Strict finality status build.",
            )
        )
        self._ledger = self._ledger.add_stage_build(
            StageBuildRecord(
                build_id=new_id("stage_build"),
                input_stage=LedgerStage.CHECKED_STATUS,
                output_stage=LedgerStage.CHECKED_ADMISSIBILITY,
                phase_start=PhaseLevel.ADMISSIBILITY_BODY,
                phase_end=PhaseLevel.CHECKED_ADMISSIBILITY,
                rule_versions=(rule_version_id,),
                checker_versions=(checker_version_id,),
                input_frontier=(status_body.id, checked_status.id, vector.id),
                emitted_records=(vector.id, admissibility_body.id, checked_admissibility.id),
                reads=(status_body.id,),
                reason="Strict finality admissibility build.",
            )
        )
        metadata = dict(self._ledger.metadata)
        metadata["kernel"] = {
            "kernel_id": "ledger-kernel",
            "validation_kernel_id": "validation-kernel",
            "object_kernel_id": "object-kernel",
        }
        self._ledger = replace(self._ledger, metadata=to_plain(metadata))  # type: ignore[arg-type]
        return self.finalize()

    def finalize(self) -> EvaluatedLedger:
        return self._ledger.freeze_through(LedgerStage.FINAL)

    def _latest_target_record(self) -> LedgerRecord | None:
        for record_type in (RecordType.CLAIM, RecordType.SUPPORT, RecordType.EVIDENCE):
            record = self._ledger.latest(record_type)
            if record is not None:
                return record
        return self._ledger.records[-1] if self._ledger.records else None

    def _has_anchor_declaration(self, anchor_id: str) -> bool:
        return any(
            record.payload.get("anchor_id") == anchor_id
            for record in self._ledger.find(RecordType.ANCHOR_DECLARATION)
        )

    def _has_adequacy_record(self, component: str) -> bool:
        return any(
            record.payload.get("component") == component
            for record in self._ledger.find(RecordType.ADEQUACY_RECORD)
        )

    def _ensure_root_debt(self) -> LedgerRecord:
        existing = self._ledger.latest(RecordType.ROOT_DEBT)
        if existing is not None:
            return existing
        record = LedgerRecord.create(
            RecordType.ROOT_DEBT,
            LedgerStage.CHECKED_CORE,
            {
                "root_declaration_id": "strict-finality-root",
                "text": "Strict finality retains visible root debt instead of hiding axioms.",
                "visible": True,
                "selected_as_obligation": False,
            },
            id=new_id("root_debt"),
            source=self.agent_id,
        )
        self._ledger = self._ledger.add_record(record)
        self.add_anchor_declaration(
            anchor_id=record.id,
            anchor_kind=AnchorKind.ROOT_DECLARATION,
            root_debt_id=record.id,
            reason="Visible root debt for strict finality kernel admission.",
        )
        return record

    def _set_validation_coordinate(
        self,
        record: LedgerRecord,
        phase: PhaseLevel,
        *,
        target_id: str = "null",
    ) -> None:
        self._ledger = replace(
            self._ledger,
            support_graph=self._ledger.support_graph.add_validation_coordinate(
                record.id,
                ValidationCoordinate(
                    event_id=record.event_id,
                    stage=record.stage,
                    phase=phase,
                    target_id=target_id,
                ),
            ),
        )

    def _add_edges(
        self,
        support_record: LedgerRecord,
        targets: list[str] | tuple[str, ...],
        *,
        role: SupportRole,
        event_id: str,
    ) -> None:
        for target_id in targets:
            self._ledger = self._ledger.add_support_edge(
                SupportEdge(
                    source_id=support_record.id,
                    target_id=target_id,
                    role=role,
                    reason=str(support_record.payload.get("text", "")),
                    event_id=event_id,
                    witness_id=support_record.id,
                )
            ).mark_checked(target_id)
