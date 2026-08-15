# Roadmap 1–4 Upgrade Notes

This package upgrades the current Responsible AI Digital Twin project in-place. It does not create a second project.

## Main additions

- Four approved local/synthetic scenarios (`SCN-001` … `SCN-004`)
- Generic scenario registry and scenario-aware LLM/fallback analysis
- Generic remediation/verification flow
- `validated` terminal lifecycle for already-secure behavior
- Run Analytics page and analytics service
- Rich PostgreSQL report reconstruction
- PDF, JSON, CSV and ZIP evidence exports
- Optional password authentication and RBAC
- `POL-SCN-001` scenario governance rule
- `POL-RBAC-001` role governance rule
- File-backed secret support
- PostgreSQL backup/restore tools
- Nginx/TLS production-style local profile
- Docker health checks/resource limits/network separation
- GitHub Actions CI and unit tests

## Database compatibility

No new schema migration is required. Existing databases remain at `005_twin_snapshots`.

## Required local actions after copying the package

1. Keep your existing `.env`.
2. Install upgraded requirements.
3. Rebuild Docker SecureMessenger.
4. Run the migration helper.
5. Start Streamlit.
6. Reset Demo and validate SCN-001 through SCN-004 one at a time.
7. Inspect Run History, Analytics, Reports, Compliance and Audit Trail.

University of Tartu server deployment is not included in this package.
