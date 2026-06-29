from __future__ import annotations

import argparse
import email.parser
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

import tomllib

EXPECTED_PROJECT = "fost-agent-ledger"
EXPECTED_VERSION = "1.0.0"
EXPECTED_REPOSITORY = "https://github.com/kadubon/fost-agent-ledger"
EXPECTED_DOI = "https://doi.org/10.5281/zenodo.20995846"


@dataclass(frozen=True)
class MetadataFinding:
    code: str
    message: str


def check_project_metadata(project_root: Path) -> list[MetadataFinding]:
    pyproject = project_root / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = data["project"]
    findings: list[MetadataFinding] = []
    if project.get("name") != EXPECTED_PROJECT:
        findings.append(MetadataFinding("metadata.name", "project name must be fost-agent-ledger"))
    if project.get("version") != EXPECTED_VERSION:
        findings.append(MetadataFinding("metadata.version", "project version must be 1.0.0"))

    urls = project.get("urls", {})
    serialized_urls = "\n".join(str(value) for value in urls.values())
    if "fost-tools" in serialized_urls:
        findings.append(
            MetadataFinding("metadata.stale_url", "project URLs contain stale fost-tools")
        )
    for key in ("Homepage", "Documentation", "Issues", "Source", "Changelog", "Security"):
        value = str(urls.get(key, ""))
        if EXPECTED_REPOSITORY not in value:
            findings.append(
                MetadataFinding(
                    "metadata.repository_url", f"project URL {key} must use kadubon repo"
                )
            )
    if urls.get("Paper") != EXPECTED_DOI:
        findings.append(
            MetadataFinding("metadata.paper_doi", "project URLs must include Paper DOI")
        )
    return findings


def check_distribution_metadata(dist_path: Path) -> list[MetadataFinding]:
    current_artifacts = _current_artifacts(dist_path)
    findings: list[MetadataFinding] = []
    if not current_artifacts:
        return [MetadataFinding("metadata.missing_dist", "no current 1.0.0 artifacts found")]
    for artifact in current_artifacts:
        metadata = _read_artifact_metadata(artifact)
        if metadata.get("Name") != EXPECTED_PROJECT:
            findings.append(
                MetadataFinding("metadata.dist_name", f"{artifact} has wrong package name")
            )
        if metadata.get("Version") != EXPECTED_VERSION:
            findings.append(
                MetadataFinding("metadata.dist_version", f"{artifact} has wrong package version")
            )
        project_urls = metadata.get_all("Project-URL", [])
        text = "\n".join(project_urls)
        if EXPECTED_REPOSITORY not in text:
            findings.append(
                MetadataFinding(
                    "metadata.dist_repository_url",
                    f"{artifact} metadata does not point at kadubon repository",
                )
            )
        if EXPECTED_DOI not in text:
            findings.append(
                MetadataFinding("metadata.dist_paper_doi", f"{artifact} metadata lacks paper DOI")
            )
        if "fost-tools" in text:
            findings.append(
                MetadataFinding("metadata.dist_stale_url", f"{artifact} metadata has stale URL")
            )
    return findings


def _current_artifacts(dist_path: Path) -> tuple[Path, ...]:
    if dist_path.is_file():
        return (dist_path,) if EXPECTED_VERSION in dist_path.name else ()
    return tuple(
        sorted(
            item
            for item in dist_path.iterdir()
            if EXPECTED_VERSION in item.name
            and (item.suffix == ".whl" or item.name.endswith(".tar.gz"))
        )
    )


def _read_artifact_metadata(artifact: Path) -> email.message.Message:
    parser = email.parser.Parser()
    if artifact.suffix == ".whl":
        with zipfile.ZipFile(artifact) as archive:
            metadata_name = next(
                name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
            )
            return parser.parsestr(archive.read(metadata_name).decode("utf-8"))
    with tarfile.open(artifact, "r:gz") as archive:
        metadata_name = next(name for name in archive.getnames() if name.endswith("/PKG-INFO"))
        extracted = archive.extractfile(metadata_name)
        if extracted is None:
            msg = f"{artifact} lacks readable PKG-INFO"
            raise ValueError(msg)
        return parser.parsestr(extracted.read().decode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check release package metadata.")
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("dist", nargs="?", default=None)
    args = parser.parse_args(argv)

    findings = check_project_metadata(Path(args.project_root))
    if args.dist is not None:
        findings.extend(check_distribution_metadata(Path(args.dist)))
    if findings:
        for finding in findings:
            print(f"{finding.code}: {finding.message}")
        return 1
    print("package metadata check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
