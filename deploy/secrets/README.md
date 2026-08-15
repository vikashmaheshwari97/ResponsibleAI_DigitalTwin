# Local hardening secret files

This directory is intentionally tracked only through this README. Actual secret files are ignored by Git.

For the local production-style hardening smoke test, create:

```text
postgres_password.txt
sandbox_admin_token.txt
admin_password_hash.txt
operator_password_hash.txt
auditor_password_hash.txt
```

Recommended helper:

```bash
python scripts/prepare_hardening_secrets.py
```

The helper generates random PostgreSQL/sandbox secrets and prompts for the three role passwords without printing them. Use `--force` only when intentionally rotating the local hardening secrets.

Validate afterwards:

```bash
python scripts/validate_hardening_config.py
```

Never commit the generated files.
