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
    respect_coordinates: tuple[str, ...] = ()
    reason: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StatusBody:
        return cls(
            body_id=str(data["body_id"]),
            target_id=str(data["target_id"]),
            support_coordinates=tuple(str(item) for item in data.get("support_coordinates", ())),
            respect_coordinates=tuple(str(item) for item in data.get("respect_coordinates", ())),
            reason=str(data.get("reason", "")),
        )


@dataclass(frozen=True)
class CheckedStatus(JsonModel):
    status_id: str
    body_record_id: str
    status: Status
    checker_version_id: str
    read_coordinates: tuple[str, ...] = ()
    respect_coordinates: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckedStatus:
        return cls(
            status_id=str(data["status_id"]),
            body_record_id=str(data["body_record_id"]),
            status=Status(data["status"]),
            checker_version_id=str(data["checker_version_id"]),
            read_coordinates=tuple(str(item) for item in data.get("read_coordinates", ())),
            respect_coordinates=tuple(str(item) for item in data.get("respect_coordinates", ())),
        )


@dataclass(frozen=True)
class AdmissibilityBody(JsonModel):
    body_id: str
    target_id: str
    status_body_record_id: str | None = None
    support_vector_id: str | None = None
    reason: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdmissibilityBody:
        return cls(
            body_id=str(data["body_id"]),
            target_id=str(data["target_id"]),
            status_body_record_id=data.get("status_body_record_id"),
            support_vector_id=data.get("support_vector_id"),
            reason=str(data.get("reason", "")),
        )


@dataclass(frozen=True)
class CheckedAdmissibility(JsonModel):
    admissibility_id: str
    body_record_id: str
    admissibility: Admissibility
    checker_version_id: str
    pre_admissibility_vector_id: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckedAdmissibility:
        return cls(
            admissibility_id=str(data["admissibility_id"]),
            body_record_id=str(data["body_record_id"]),
            admissibility=Admissibility(data["admissibility"]),
            checker_version_id=str(data["checker_version_id"]),
            pre_admissibility_vector_id=str(data["pre_admissibility_vector_id"]),
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
    support_coordinates: tuple[str, ...] = ()
    validator_coordinates: tuple[str, ...] = ()
    kernel_coordinates: tuple[str, ...] = ()
    certificate_coordinates: tuple[str, ...] = ()
    environment_coordinates: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PreAdmissibilitySupportVector:
        return cls(
            vector_id=str(data["vector_id"]),
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
        )
