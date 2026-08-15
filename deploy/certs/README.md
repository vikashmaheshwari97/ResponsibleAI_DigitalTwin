# Local TLS smoke-test material

This directory is intentionally tracked only through this README. Generated certificates and private keys are ignored by Git.

For a local production-style smoke test, generate a self-signed certificate with one of the existing helpers:

PowerShell:

```powershell
./scripts/generate_local_tls.ps1
```

WSL/Linux:

```bash
bash scripts/generate_local_tls.sh
```

Expected files:

```text
server.crt
server.key
```

Then run:

```bash
python scripts/validate_hardening_config.py
```

A real University of Tartu deployment must use certificate management approved for the target infrastructure; the self-signed local certificate is only for smoke testing.
