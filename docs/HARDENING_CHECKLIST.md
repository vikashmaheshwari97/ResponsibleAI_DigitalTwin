# Local Deployment-Hardening Checklist

This checklist validates hardening locally before any future University of Tartu deployment.

## Secrets

- [ ] `.env` is ignored by Git.
- [ ] No legacy development password/token is hard-coded in tracked source.
- [ ] File-backed deployment secrets exist only under `deploy/secrets/`.
- [ ] Admin, operator and auditor bcrypt hashes are configured.

Prepare local hardening secret files:

```bash
python scripts/prepare_hardening_secrets.py
```

## TLS / reverse proxy

- [ ] Nginx TLS profile exists.
- [ ] Local smoke-test certificate/key generated.
- [ ] Streamlit WebSocket proxying works through HTTPS.
- [ ] Security headers are visible in the reverse-proxy response.

## PostgreSQL resilience

- [ ] A fresh `.sql.gz` backup exists.
- [ ] Backup gzip integrity passes.
- [ ] Backup resembles a PostgreSQL dump.
- [ ] Restore procedure is documented and requires explicit confirmation.

Commands:

```bash
python scripts/backup_database.py
python scripts/verify_backup.py
```

## Containers / network

- [ ] CPU and memory limits are present.
- [ ] Services use restart policies and health checks.
- [ ] Production backend network is internal-only.
- [ ] PostgreSQL and SecureMessenger are not host-published in the production-style profile.

## CI / regression

- [ ] Syntax compilation passes.
- [ ] Ruff safety checks pass.
- [ ] Unit tests pass.
- [ ] Four sandbox contract tests pass.
- [ ] Evidence bundle manifest test passes.
- [ ] Compose configuration validation passes.

Validate:

```bash
python scripts/validate_hardening_config.py
```

The University of Tartu deployment is a later milestone and is not performed by these scripts.

## Hardened runtime smoke test

After the configuration validator passes:

```bash
docker compose -f docker-compose.prod.yml up -d --build
python scripts/smoke_hardened_runtime.py
```

The runtime smoke test checks HTTPS health, reverse-proxy security headers, container state, and that PostgreSQL/SecureMessenger have no host-published ports in the production-style profile.
