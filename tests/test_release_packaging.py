from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from tools.audit_release import audit_paths
from tools.check_package_metadata import check_project_metadata

DOI = "https://doi.org/10.5281/zenodo.20995846"
REPOSITORY = "https://github.com/kadubon/fost-agent-ledger"


def test_release_workflow_matches_pypi_trusted_publisher_contract() -> None:
    workflow_path = Path(".github/workflows/workflow.yml")
    assert workflow_path.is_file()
    assert not Path(".github/workflows/publish.yml").exists()

    workflow = workflow_path.read_text(encoding="utf-8")
    assert "release:" in workflow
    assert 'types: ["published"]' in workflow
    assert "environment: pypi" in workflow
    assert "id-token: write" in workflow
    assert "contents: read" in workflow
    assert "uv publish --trusted-publishing always" in workflow
    assert "secrets." not in workflow
    assert "PYPI_API_TOKEN" not in workflow
    assert "UV_PUBLISH_TOKEN" not in workflow


def test_project_metadata_is_ready_for_pypi() -> None:
    assert check_project_metadata(Path(".")) == []
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert REPOSITORY in pyproject
    assert DOI in pyproject
    assert "fost-tools" not in pyproject


def test_public_docs_and_workflows_have_no_local_paths_or_stale_urls() -> None:
    public_paths = [
        Path("README.md"),
        Path("CHANGELOG.md"),
        Path("SECURITY.md"),
        Path("CONTRIBUTING.md"),
        Path("CODE_OF_CONDUCT.md"),
        Path("pyproject.toml"),
        *sorted(Path("docs").glob("*.md")),
        *sorted(Path(".github/workflows").glob("*.yml")),
    ]
    public_text = "\n".join(path.read_text(encoding="utf-8") for path in public_paths)
    assert "fost-tools" not in public_text
    assert ("C:" + "\\Users\\") not in public_text
    assert ("/" + "home/") not in public_text
    assert ("." + "codex") not in public_text
    assert ("Desk" + "top") not in public_text
    assert DOI in public_text


def test_artifact_audit_accepts_clean_wheel(tmp_path: Path) -> None:
    wheel = tmp_path / "clean-0.0.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("clean/__init__.py", 'TOKEN_KIND = "public enum name"\n')
        archive.writestr("clean-0.0.0.dist-info/METADATA", "Name: clean\nVersion: 0.0.0\n")
    assert audit_paths([wheel]) == []


def test_artifact_audit_rejects_public_hygiene_failures(tmp_path: Path) -> None:
    sdist = tmp_path / "bad-0.0.0.tar.gz"
    local_path = "C:" + "\\Users\\someone\\" + "Desk" + "top" + "\\secret.txt"
    secret_assignment = ("OPENAI" + "_API_KEY") + "=" + ("sk-" + "x" * 32)
    private_key = "-----BEGIN " + "PRIVATE KEY-----"
    entries = {
        "bad-0.0.0/.env": "SHOULD_NOT_SHIP=1",
        "bad-0.0.0/bad.pyc": "compiled",
        "bad-0.0.0/module.py": f"{local_path}\n{secret_assignment}\n{private_key}\n",
    }
    with tarfile.open(sdist, "w:gz") as archive:
        for name, text in entries.items():
            encoded = text.encode("utf-8")
            info = tarfile.TarInfo(name)
            info.size = len(encoded)
            archive.addfile(info, io.BytesIO(encoded))

    codes = {finding.code for finding in audit_paths([sdist])}
    assert "artifact.unwanted_member" in codes
    assert "artifact.local_path" in codes
    assert "artifact.private_key" in codes
    assert "artifact.secret_like_assignment" in codes


def test_current_built_artifacts_pass_when_present() -> None:
    artifacts = sorted(Path("dist").glob("fost_agent_ledger-1.0.0*"))
    if not artifacts:
        pytest.skip("1.0.0 artifacts are created by the build step")
    assert audit_paths(artifacts) == []
