# TLS certificates

Do not commit private keys or certificates generated for a real environment.

For a local HTTPS smoke test, generate a self-signed certificate with:

- PowerShell: `./scripts/generate_local_tls.ps1`
- Linux/WSL: `bash scripts/generate_local_tls.sh`

This creates `server.crt` and `server.key` in this directory. Both are ignored by Git.
