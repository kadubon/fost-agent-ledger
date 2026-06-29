from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fost_agent_ledger import LedgerBuilder, validate_ledger
from fost_agent_ledger.certificates import (
    Certificate,
    CertificateRegistry,
    CertificateState,
    CertificateTarget,
    CertificateUse,
    RequiredCertificate,
)


def main() -> None:
    builder = LedgerBuilder(agent_id="agent-1", mode="draft")
    claim = builder.add_claim("A certificate is used only for its explicit target.")
    builder.add_support("The certificate target registry records the target.", supports=[claim.id])
    cert = Certificate(
        certificate_id="cert-1",
        issuer="example-issuer",
        scope={"mode": "draft"},
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    target = CertificateTarget(
        target_id="target-1",
        judgment_kind="policy",
        use_kind="cover",
        target_node=claim.id,
        event_id="event-0",
        scope={"mode": "draft"},
        required=True,
    )
    use = CertificateUse.create(
        certificate_id=cert.certificate_id,
        target_id=target.target_id,
        judgment_kind="policy",
        use_kind="cover",
        target_node=claim.id,
    )
    state = CertificateState(
        state_id="cert-state-1",
        certificate_id=cert.certificate_id,
        target_id=target.target_id,
        state="ok",
        target_node=claim.id,
    )
    registry = CertificateRegistry(
        certificates=(cert,),
        targets=(target,),
        required=(
            RequiredCertificate(
                target_id=target.target_id,
                certificate_id=cert.certificate_id,
            ),
        ),
        uses=(use,),
        states=(state,),
    )
    print(validate_ledger(builder.finalize(), certificate_registry=registry).summary)


if __name__ == "__main__":
    main()
