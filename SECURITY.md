# Security and Responsible Use

This repository is a research proof of concept for a Digital-Twin-Driven Responsible AI platform.

## Supported security-testing boundary

The implemented validation scenarios are intentionally limited to:

- the local Docker `SecureMessenger` sandbox;
- synthetic users, tokens, messages and payloads;
- the predefined scenario registry `SCN-001` through `SCN-004`;
- defensive remediation;
- explicit human approval before security-changing actions; and
- post-remediation verification.

The UI does not accept arbitrary external targets. Do not modify the project to test systems you do not own or lack explicit authorization to assess.

## Secrets

Never commit:

- `.env`;
- database passwords;
- sandbox admin tokens;
- password hashes;
- TLS private keys; or
- files generated under `deploy/secrets/` and `deploy/certs/`.

The repository contains `.gitignore` rules for these local materials. Run the readiness validator and CI secret scan before pushing changes.

## Reporting a repository security issue

If you discover a security issue in this research code, avoid publishing exploitable secrets or private data in a public issue. Contact the repository owner through an appropriate private channel first when sensitive details are involved.
