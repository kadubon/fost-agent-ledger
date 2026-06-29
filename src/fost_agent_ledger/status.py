from __future__ import annotations

from .enums import ProblemSeverity, RecordType, Status
from .ledger import EvaluatedLedger
from .model import Problem


def evaluate_status(ledger: EvaluatedLedger, problems: tuple[Problem, ...] = ()) -> Status:
    """Compute the finite ledger status without deciding admissibility."""

    severities = {problem.severity for problem in problems}
    if ProblemSeverity.ERROR in severities:
        return Status.INVALID
    if ProblemSeverity.BLOCKER in severities:
        return Status.BLOCKED
    if not ledger.find(RecordType.CLAIM):
        return Status.UNKNOWN
    if not (ledger.find(RecordType.SUPPORT) or ledger.find(RecordType.EVIDENCE)):
        return Status.UNSUPPORTED
    if ProblemSeverity.WARNING in severities or ledger.find(RecordType.ISSUE):
        return Status.PARTIAL
    return Status.SUPPORTED
