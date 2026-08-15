# Deployment secrets

The hardened Compose profile uses file-backed secrets. Create these files locally and never commit them:

- `postgres_password.txt`
- `sandbox_admin_token.txt`
- `admin_password_hash.txt`
- `operator_password_hash.txt`
- `auditor_password_hash.txt`

Generate bcrypt password hashes with:

```bash
python scripts/generate_password_hash.py
```

Files in this directory are ignored by Git except this README.
