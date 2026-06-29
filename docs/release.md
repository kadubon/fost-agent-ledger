# Release And PyPI Publishing

This repository is prepared for PyPI Trusted Publishing through GitHub Actions.

## PyPI Pending Publisher

Create the pending publisher on PyPI with these exact fields:

- Project name: `fost-agent-ledger`
- Publisher: GitHub
- Owner: `kadubon`
- Repository: `fost-agent-ledger`
- Workflow: `workflow.yml`
- Environment name: `pypi`

The workflow file is `.github/workflows/workflow.yml`. It publishes only when a GitHub Release is published.

## What The Workflow Does

1. Checks formatting, lint, types, tests, and build.
2. Audits release artifacts for caches, local paths, local workspace markers, private keys, and secret-like assignments.
3. Checks package metadata for the `kadubon/fost-agent-ledger` repository URLs and paper DOI.
4. Publishes with OIDC Trusted Publishing using `uv publish --trusted-publishing always`.

No PyPI password, API token, or GitHub secret is required for the publish step.

## Operator Actions

The code prepares and validates the publishing path. The operator still performs these external actions:

- create or connect the GitHub repository `kadubon/fost-agent-ledger`;
- configure the PyPI pending publisher with the exact fields above;
- configure any GitHub environment protection rules for `pypi`;
- create and publish the GitHub Release when the package should be uploaded.

Do not publish from a local machine with a long-lived PyPI token unless Trusted Publishing is unavailable.
