from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .enums import Admissibility, Status
from .model import JsonModel


@dataclass(frozen=True)
class StatusBody(JsonModel):
    body_id: str
    target_id: str
    support_coordinates: tuple[str, ...] = ()
    read_coordinates: tuple[str, ...] = ()
    respect_coordinates: tuple[str, ...] = ()
    checker_version_id: str = ""
    rule_version_id: str = ""
    reads_final_output: bool = False
    reason: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StatusBody:
        return cls(
            body_id=str(data["body_id"]),
            target_id=str(data["target_id"]),
            support_coordinates=tuple(str(item) for item in data.get("support_coordinates", ())),
            read_coordinates=tuple(str(item) for item in data.get("read_coordinates", ())),
            respect_coordinates=tuple(str(item) for item in data.get("respect_coordinates", ())),
            checker_version_id=str(data.get("checker_version_id", "")),
            rule_version_id=str(data.get("rule_version_id", "")),
            reads_final_output=bool(data.get("reads_final_output", False)),
            reason=str(data.get("reason", "")),
        )


@dataclass(frozen=True)
class CheckedStatus(JsonModel):
    status_id: str
    body_record_id: str
    status: Status
    checker_version_id: str
    rule_version_id: str = ""
    read_coordinates: tuple[str, ...] = ()
    respect_coordinates: tuple[str, ...] = ()
    checked: bool = True
    reads_final_output: bool = False
    reason: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckedStatus:
        return cls(
            status_id=str(data["status_id"]),
            body_record_id=str(data["body_record_id"]),
            status=Status(data["status"]),
            checker_version_id=str(data["checker_version_id"]),
            rule_version_id=str(data.get("rule_version_id", "")),
            read_coordinates=tuple(str(item) for item in data.get("read_coordinates", ())),
            respect_coordinates=tuple(str(item) for item in data.get("respect_coordinates", ())),
            checked=bool(data.get("checked", True)),
            reads_final_output=bool(data.get("reads_final_output", False)),
            reason=str(data.get("reason", "")),
        )


@dataclass(frozen=True)
class AdmissibilityBody(JsonModel):
    body_id: str
    target_id: str
    status_body_record_id: str | None = None
    pre_admissibility_vector_id: str | None = None
    support_coordinates: tuple[str, ...] = ()
    read_coordinates: tuple[str, ...] = ()
    respect_coordinates: tuple[str, ...] = ()
    checker_version_id: str = ""
    rule_version_id: str = ""
    reads_final_output: bool = False
    reason: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdmissibilityBody:
        return cls(
            body_id=str(data["body_id"]),
            target_id=str(data["target_id"]),
            status_body_record_id=data.get("status_body_record_id"),
            pre_admissibility_vector_id=data.get(
                "pre_admissibility_vector_id", data.get("support_vector_id")
            ),
            support_coordinates=tuple(str(item) for item in data.get("support_coordinates", ())),
            read_coordinates=tuple(str(item) for item in data.get("read_coordinates", ())),
            respect_coordinates=tuple(str(item) for item in data.get("respect_coordinates", ())),
            checker_version_id=str(data.get("checker_version_id", "")),
            rule_version_id=str(data.get("rule_version_id", "")),
            reads_final_output=bool(data.get("reads_final_output", False)),
            reason=str(data.get("reason", "")),
        )


@dataclass(frozen=True)
class CheckedAdmissibility(JsonModel):
    admissibility_id: str
    body_record_id: str
    admissibility: Admissibility
    checker_version_id: str
    pre_admissibility_vector_id: str
    rule_version_id: str = ""
    read_coordinates: tuple[str, ...] = ()
    respect_coordinates: tuple[str, ...] = ()
    checked: bool = True
    reads_final_output: bool = False
    reason: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckedAdmissibility:
        return cls(
            admissibility_id=str(data["admissibility_id"]),
            body_record_id=str(data["body_record_id"]),
            admissibility=Admissibility(data["admissibility"]),
            checker_version_id=str(data["checker_version_id"]),
            pre_admissibility_vector_id=str(data["pre_admissibility_vector_id"]),
            rule_version_id=str(data.get("rule_version_id", "")),
            read_coordinates=tuple(str(item) for item in data.get("read_coordinates", ())),
            respect_coordinates=tuple(str(item) for item in data.get("respect_coordinates", ())),
            checked=bool(data.get("checked", True)),
            reads_final_output=bool(data.get("reads_final_output", False)),
            reason=str(data.get("reason", "")),
        )


@dataclass(frozen=True)
class RespectRecord(JsonModel):
    respect_id: str
    coordinate: str
    respected: bool
    reason: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RespectRecord:
        return cls(
            respect_id=str(data["respect_id"]),
            coordinate=str(data["coordinate"]),
            respected=bool(data["respected"]),
            reason=str(data.get("reason", "")),
        )


@dataclass(frozen=True)
class PreAdmissibilitySupportVector(JsonModel):
    vector_id: str
    target_id: str = ""
    support_coordinates: tuple[str, ...] = ()
    validator_coordinates: tuple[str, ...] = ()
    kernel_coordinates: tuple[str, ...] = ()
    certificate_coordinates: tuple[str, ...] = ()
    environment_coordinates: tuple[str, ...] = ()
    obligation_coordinates: tuple[str, ...] = ()
    adequacy_coordinates: tuple[str, ...] = ()
    checker_version_id: str = ""
    rule_version_id: str = ""
    reason: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PreAdmissibilitySupportVector:
        return cls(
            vector_id=str(data["vector_id"]),
            target_id=str(data.get("target_id", "")),
            support_coordinates=tuple(str(item) for item in data.get("support_coordinates", ())),
            validator_coordinates=tuple(
                str(item) for item in data.get("validator_coordinates", ())
            ),
            kernel_coordinates=tuple(str(item) for item in data.get("kernel_coordinates", ())),
            certificate_coordinates=tuple(
                str(item) for item in data.get("certificate_coordinates", ())
            ),
            environment_coordinates=tuple(
                str(item) for item in data.get("environment_coordinates", ())
            ),
            obligation_coordinates=tuple(
                str(item) for item in data.get("obligation_coordinates", ())
            ),
            adequacy_coordinates=tuple(str(item) for item in data.get("adequacy_coordinates", ())),
            checker_version_id=str(data.get("checker_version_id", "")),
            rule_version_id=str(data.get("rule_version_id", "")),
            reason=str(data.get("reason", "")),
        )
