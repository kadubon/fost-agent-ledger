# Certificates

A certificate is not generally valid. It is valid only for an explicit target.

## Required Pieces

- `certificate`: issuer, scope, issued time, optional expiry, metadata.
- `certificate_target`: target ID, judgment kind, use kind, target node, event, scope, target state.
- `certificate_use`: which certificate was used for which target.
- `certificate_state`: the checked finite state for that use.
- role-compatible support edge from certificate-state node to target node.

## Common Failures

- Missing target: `certificate.missing_target`
- Expired used certificate: `certificate.expired`
- Scope mismatch: `certificate.scope_fail`
- Missing certificate-state node: `certificate.missing_state`
- Null certificate misuse: `certificate.null_misuse`
- Circular certificate/kernel support: `certificate.kernel_circular_support`

## Operational Rule

Keep certificates narrow. Register the target first, then add the use and state. Do not reuse one certificate as a general truth or safety stamp.
