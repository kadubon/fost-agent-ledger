from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import DEFAULT_STAGE_PHASE, PHASE_ORDER, STAGE_ORDER, LedgerStage, PhaseLevel
from .model import JsonDict, JsonModel, Problem


def stage_index(stage: LedgerStage | str) -> int:
    return STAGE_ORDER.index(LedgerStage(stage))


def phase_index(phase: PhaseLevel | str) -> int:
    return PHASE_ORDER.index(PhaseLevel(phase))


@dataclass(frozen=True)
class ValidationCoordinate(JsonModel):
    event_id: str
    stage: LedgerStage
    phase: PhaseLevel
    target_id: str = "null"

    def key(self, event_position: int = 0) -> tuple[int, int, int, str]:
        return (event_position, stage_index(self.stage), phase_index(self.phase), self.target_id)

    @classmethod
    def default_for_record(
        cls,
        *,
        event_id: str,
        stage: LedgerStage | str,
        target_id: str = "null",
    ) -> ValidationCoordinate:
        ledger_stage = LedgerStage(stage)
        return cls(
            event_id=event_id,
            stage=ledger_stage,
            phase=DEFAULT_STAGE_PHASE[ledger_stage],
            target_id=target_id,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ValidationCoordinate:
        return cls(
            event_id=str(data.get("event_id", "event-0")),
            stage=LedgerStage(data["stage"]),
            phase=PhaseLevel(data["phase"]),
            target_id=str(data.get("target_id", "null")),
        )


@dataclass(frozen=True)
class StageBuildRecord(JsonModel):
    build_id: str
    input_stage: LedgerStage
    output_stage: LedgerStage
    phase_start: PhaseLevel
    phase_end: PhaseLevel
    event_id: str = "event-0"
    rule_versions: tuple[str, ...] = ()
    checker_versions: tuple[str, ...] = ()
    input_frontier: tuple[str, ...] = ()
    emitted_records: tuple[str, ...] = ()
    reads: tuple[str, ...] = ()
    reason: str = ""
    metadata: JsonDict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StageBuildRecord:
        return cls(
            build_id=str(data["build_id"]),
            input_stage=LedgerStage(data["input_stage"]),
            output_stage=LedgerStage(data["output_stage"]),
            phase_start=PhaseLevel(data["phase_start"]),
            phase_end=PhaseLevel(data["phase_end"]),
            event_id=str(data.get("event_id", "event-0")),
            rule_versions=tuple(str(item) for item in data.get("rule_versions", ())),
            checker_versions=tuple(str(item) for item in data.get("checker_versions", ())),
            input_frontier=tuple(str(item) for item in data.get("input_frontier", ())),
            emitted_records=tuple(str(item) for item in data.get("emitted_records", ())),
            reads=tuple(str(item) for item in data.get("reads", ())),
            reason=str(data.get("reason", "")),
            metadata=dict(data.get("metadata", {})),
        )


def validate_stage_builds(
    *,
    stage_builds: tuple[StageBuildRecord, ...],
    record_stages: dict[str, LedgerStage],
) -> tuple[Problem, ...]:
    from .enums import ProblemSeverity

    problems: list[Problem] = []
    for build in stage_builds:
        if stage_index(build.input_stage) > stage_index(build.output_stage):
            problems.append(
                Problem(
                    code="stage.invalid_build_order",
                    message="stage build input stage is later than output stage",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(build.build_id,),
                )
            )
        if phase_index(build.phase_start) > phase_index(build.phase_end):
            problems.append(
                Problem(
                    code="stage.invalid_phase_interval",
                    message="stage build phase interval is reversed",
                    severity=ProblemSeverity.ERROR,
                    related_record_ids=(build.build_id,),
                )
            )
        for emitted in build.emitted_records:
            emitted_stage = record_stages.get(emitted)
            if emitted_stage is not None and emitted_stage != build.output_stage:
                problems.append(
                    Problem(
                        code="stage.emitted_stage_mismatch",
                        message="stage build emitted record has a different output stage",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(build.build_id, emitted),
                    )
                )
        for read in build.reads:
            read_stage = record_stages.get(read)
            if read_stage is not None and stage_index(read_stage) > stage_index(build.input_stage):
                problems.append(
                    Problem(
                        code="stage.forbidden_future_read",
                        message="stage build reads a record outside its permitted lower stage",
                        severity=ProblemSeverity.ERROR,
                        related_record_ids=(build.build_id, read),
                    )
                )
    return tuple(problems)
