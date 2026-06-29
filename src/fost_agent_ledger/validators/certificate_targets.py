from __future__ import annotations

from ..certificates import CertificateRegistry
from ..ledger import EvaluatedLedger
from ..model import Problem


def validate_certificate_targets(
    ledger: EvaluatedLedger,
    registry: CertificateRegistry,
) -> tuple[Problem, ...]:
    return registry.validate(support_graph=ledger.support_graph)
