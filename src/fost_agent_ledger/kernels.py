from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import (
    KernelAdmissionBasisKind,
    KernelAdmissionKind,
    KernelAdmissionStatus,
    ProblemSeverity,
)
from .ids import new_id
from .model import JsonDict, JsonModel, Problem


@dataclass(frozen=True)
class RuleVersion(JsonModel):
    version_id: str
    name: str
    version: str
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True)
class CheckerVersion(JsonModel):
    version_id: str
    name: str
    version: str
    metadata: JsonDict = field(default_factory=dict)


@dataclass(frozen=True)
class RootDeclaration(JsonModel):
    declaration_id: str
    text: str
    emits_root_debt: bool = True
    reason: str = ""

    @classmethod
    def create(
        cls, text: str, *, reason: str = "", emits_root_debt: bool = True
    ) -> RootDeclaration:
        return cls(new_id("root"), text, emits_root_debt, reason)


@dataclass(frozen=True)
class RootDebtRecord(JsonModel):
    debt_id: str
    root_declaration_id: str
    text: str
    visible: bool = True


@dataclass(frozen=True)
class KernelAdmission(JsonModel):
    admission_id: str
    version_id: str
    kind: KernelAdmissionKind
    status: KernelAdmissionStatus
    basis_kind: KernelAdmissionBasisKind
    checker_version_id: str
    event_id: str = "event-0"
    basis_id: str | None = None
    root_debt_id: str | None = None
    reason: str = ""
    metadata: JsonDict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KernelAdmission:
        return cls(
            admission_id=str(data["admission_id"]),
            version_id=str(data["version_id"]),
            kind=KernelAdmissionKind(data["kind"]),
            status=KernelAdmissionStatus(data["status"]),
            basis_kind=KernelAdmissionBasisKind(data["basis_kind"]),
            checker_version_id=str(data["checker_version_id"]),
            event_id=str(data.get("event_id", "event-0")),
            basis_id=data.get("basis_id"),
            root_debt_id=data.get("root_debt_id"),
            reason=str(data.get("reason", "")),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class Kernel(JsonModel):
    kernel_id: str
    validation_kernel_id: str
    object_kernel_id: str
    root_declarations: tuple[RootDeclaration, ...] = ()
    admissions: tuple[KernelAdmission, ...] = ()
    root_debts: tuple[RootDebtRecord, ...] = ()
    metadata: JsonDict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Kernel:
        return cls(
            kernel_id=str(data["kernel_id"]),
            validation_kernel_id=str(data["validation_kernel_id"]),
            object_kernel_id=str(data["object_kernel_id"]),
            root_declarations=tuple(
                RootDeclaration(**item)
                for item in data.get("root_declarations", ())
                if isinstance(item, dict)
            ),
            admissions=tuple(
                KernelAdmission.from_dict(item)
                for item in data.get("admissions", ())
                if isinstance(item, dict)
            ),
            root_debts=tuple(
                RootDebtRecord(**item)
                for item in data.get("root_debts", ())
                if isinstance(item, dict)
            ),
            metadata=dict(data.get("metadata", {})),
        )

    @classmethod
    def from_ledger(cls, ledger: Any) -> Kernel | None:
        from .enums import AnchorKind, RecordType

        admissions = tuple(
            KernelAdmission.from_dict(record.payload)
            for record in ledger.find(RecordType.KERNEL_ADMISSION)
        )
        root_debts = tuple(
            RootDebtRecord(
                debt_id=str(record.id),
                root_declaration_id=str(record.payload.get("root_declaration_id", "")),
                text=str(record.payload.get("text", "")),
                visible=bool(record.payload.get("visible", True)),
            )
            for record in ledger.find(RecordType.ROOT_DEBT)
        )
        root_declarations = tuple(
            RootDeclaration(
                declaration_id=str(record.payload.get("anchor_id", record.id)),
                text=str(record.payload.get("reason", "")),
                emits_root_debt=record.payload.get("root_debt_id") is not None,
                reason=str(record.payload.get("reason", "")),
            )
            for record in ledger.find(RecordType.ANCHOR_DECLARATION)
            if record.payload.get("anchor_kind") == AnchorKind.ROOT_DECLARATION.value
        )
        metadata = (
            dict(ledger.metadata.get("kernel", {})) if isinstance(ledger.metadata, dict) else {}
        )
        if not admissions and not root_debts and not root_declarations and not metadata:
            return None
        return cls(
            kernel_id=str(metadata.get("kernel_id", "ledger-kernel")),
            validation_kernel_id=str(metadata.get("validation_kernel_id", "validation-kernel")),
            object_kernel_id=str(metadata.get("object_kernel_id", "object-kernel")),
            root_declarations=root_declarations,
            admissions=admissions,
            root_debts=root_debts,
            metadata=metadata,
        )


def validate_kernel(kernel: Kernel) -> tuple[Problem, ...]:
    problems: list[Problem] = []
    if kernel.validation_kernel_id == kernel.object_kernel_id:
        problems.append(
            Problem(
                code="kernel.validation_equals_object",
                message="validation kernel and object kernel must remain distinct for admission",
                severity=ProblemSeverity.ERROR,
                related_record_ids=(kernel.kernel_id,),
            )
        )
    visible_debts = {debt.debt_id for debt in kernel.root_debts if debt.visible}
    admissions_by_version: dict[str, set[KernelAdmissionStatus]] = {}
    for admission in kernel.admissions:
        admissions_by_version.setdefault(admission.version_id, set()).add(admission.status)
    for version_id, statuses in admissions_by_version.items():
        if len(statuses) > 1:
            problems.append(
                Problem(
                    code="kernel.version_view_conflict",
                    message="kernel version has incompatible maximal admission statuses",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(version_id,),
                )
            )
    if kernel.metadata.get("root_debt_reads_mode_policy", False):
        problems.append(
            Problem(
                code="kernel.root_debt_mode_selection_cycle",
                message="root debt selection cannot depend on mode-policy outputs",
                severity=ProblemSeverity.ERROR,
                related_record_ids=(kernel.kernel_id,),
            )
        )
    for admission in kernel.admissions:
        if admission.status != KernelAdmissionStatus.ADMITTED:
            continue
        if admission.basis_kind == KernelAdmissionBasisKind.SELF:
            problems.append(
                Problem(
                    code="kernel.self_certification",
                    message="new rule or checker version cannot be admitted solely by itself",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(admission.admission_id, admission.version_id),
                )
            )
        prior_or_external = {
            KernelAdmissionBasisKind.PRIOR_KERNEL,
            KernelAdmissionBasisKind.EXTERNAL_CERTIFICATE,
        }
        if (
            admission.version_id == admission.checker_version_id
            and admission.basis_kind not in prior_or_external
        ):
            problems.append(
                Problem(
                    code="kernel.checker_self_admission",
                    message="checker version admission lacks prior-kernel or external support",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(admission.admission_id, admission.version_id),
                )
            )
        if admission.basis_kind == KernelAdmissionBasisKind.PRIOR_KERNEL and not admission.basis_id:
            problems.append(
                Problem(
                    code="kernel.missing_prior_kernel_witness",
                    message="prior-kernel admission requires a finite prior-kernel witness",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(admission.admission_id, admission.version_id),
                )
            )
        if (
            admission.basis_kind == KernelAdmissionBasisKind.EXTERNAL_CERTIFICATE
            and not admission.basis_id
        ):
            problems.append(
                Problem(
                    code="kernel.missing_external_certificate_anchor",
                    message="external-certificate admission requires a finite certificate anchor",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(admission.admission_id, admission.version_id),
                )
            )
        if (
            admission.basis_kind == KernelAdmissionBasisKind.ROOT
            and admission.root_debt_id not in visible_debts
        ):
            problems.append(
                Problem(
                    code="kernel.root_debt_hidden",
                    message="root-based admission must keep root debt visible",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(admission.admission_id,),
                )
            )
        generic_reason = admission.reason.strip().lower()
        if generic_reason in {"valid", "validated", "kernel valid", "self valid"}:
            problems.append(
                Problem(
                    code="kernel.generic_validation_wording",
                    message="kernel admission reason is too generic to witness admission",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(admission.admission_id, admission.version_id),
                )
            )
    return tuple(problems)
