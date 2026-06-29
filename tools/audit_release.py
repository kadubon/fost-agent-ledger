from __future__ import annotations

import argparse
import json
import re
import tarfile
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

UNWANTED_PATH_COMPONENTS = (
    "__pycache__",
    ".coverage",
    ".env",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "." + "codex",
)

UNWANTED_SUFFIXES = (".pyc", ".pyo")

LOCAL_PATH_PATTERNS = (
    re.compile(rb"C:" + rb"\\Users\\", re.IGNORECASE),
    re.compile(rb"/" + rb"Users/[^/\s]+/"),
    re.compile(rb"/" + rb"home/[^/\s]+/"),
    re.compile(rb"\." + rb"codex", re.IGNORECASE),
    re.compile(rb"Desk" + rb"top", re.IGNORECASE),
)

PRIVATE_KEY_PATTERN = re.compile(rb"-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")

SECRET_ASSIGNMENT_PATTERN = re.compile(
    rb"(?i)\b(?:"
    rb"aws_access_key_id|aws_secret_access_key|azure_client_secret|"
    rb"github_token|gitlab_token|openai_api_key|pypi_token|twine_password|"
    rb"password|secret_key"
    rb")\b\s*[:=]\s*['\"]?[A-Za-z0-9_./+=:@-]{8,}"
)


@dataclass(frozen=True)
class AuditFinding:
    artifact: str
    member: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "artifact": self.artifact,
            "member": self.member,
            "code": self.code,
            "message": self.message,
        }


def audit_paths(paths: Iterable[Path]) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for path in paths:
        if path.is_dir():
            artifacts = sorted(
                item
                for item in path.iterdir()
                if item.suffix == ".whl" or item.name.endswith(".tar.gz")
            )
            findings.extend(audit_paths(artifacts))
            continue
        findings.extend(_audit_artifact(path))
    return findings


def _audit_artifact(path: Path) -> list[AuditFinding]:
    if path.suffix == ".whl":
        return _audit_zip(path)
    if path.name.endswith(".tar.gz"):
        return _audit_tar(path)
    return [
        AuditFinding(
            artifact=str(path),
            member="",
            code="artifact.unsupported",
            message="release audit only accepts wheel and sdist tar.gz artifacts",
        )
    ]


def _audit_zip(path: Path) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    with zipfile.ZipFile(path) as archive:
        for member in archive.namelist():
            findings.extend(_audit_member_name(path, member))
            if member.endswith("/"):
                continue
            findings.extend(_audit_content(path, member, archive.read(member)))
    return findings


def _audit_tar(path: Path) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    with tarfile.open(path, "r:gz") as archive:
        for member in archive.getmembers():
            findings.extend(_audit_member_name(path, member.name))
            if not member.isfile():
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                continue
            findings.extend(_audit_content(path, member.name, extracted.read()))
    return findings


def _audit_member_name(path: Path, member: str) -> list[AuditFinding]:
    normalized = member.replace("\\", "/")
    components = tuple(part for part in normalized.split("/") if part)
    findings: list[AuditFinding] = []
    for part in UNWANTED_PATH_COMPONENTS:
        if part in components:
            findings.append(
                AuditFinding(
                    artifact=str(path),
                    member=member,
                    code="artifact.unwanted_member",
                    message=f"artifact contains unwanted public member marker {part!r}",
                )
            )
    if normalized.endswith(UNWANTED_SUFFIXES):
        findings.append(
            AuditFinding(
                artifact=str(path),
                member=member,
                code="artifact.unwanted_member",
                message="artifact contains unwanted compiled Python member",
            )
        )
    return findings


def _audit_content(path: Path, member: str, data: bytes) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for pattern in LOCAL_PATH_PATTERNS:
        if pattern.search(data):
            findings.append(
                AuditFinding(
                    artifact=str(path),
                    member=member,
                    code="artifact.local_path",
                    message="artifact content contains a local path or local workspace marker",
                )
            )
            break
    if PRIVATE_KEY_PATTERN.search(data):
        findings.append(
            AuditFinding(
                artifact=str(path),
                member=member,
                code="artifact.private_key",
                message="artifact content contains a private key marker",
            )
        )
    if SECRET_ASSIGNMENT_PATTERN.search(data):
        findings.append(
            AuditFinding(
                artifact=str(path),
                member=member,
                code="artifact.secret_like_assignment",
                message="artifact content contains a secret-like assignment",
            )
        )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit public release artifacts.")
    parser.add_argument(
        "paths",
        nargs="*",
        default=["dist"],
        help="Wheel/sdist files or directories containing release artifacts.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    findings = audit_paths(Path(path) for path in args.paths)
    if args.json:
        print(json.dumps([finding.to_dict() for finding in findings], indent=2, sort_keys=True))
    elif findings:
        for finding in findings:
            print(f"{finding.code}: {finding.artifact}:{finding.member}: {finding.message}")
    else:
        print("release artifact audit passed")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
