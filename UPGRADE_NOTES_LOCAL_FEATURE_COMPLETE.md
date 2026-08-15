# Local Feature-Complete & Hardening Validation Upgrade

Version: `0.5.0-local-feature-complete`

This package upgrades the existing `ResponsibleAI_DigitalTwin` project in-place. It does not create a second project and does not change the core PostgreSQL schema.

## What was already complete before this package

Roadmap items 1-3 were already implemented:

1. Four approved controlled synthetic scenarios.
2. PostgreSQL-backed professional Run Analytics.
3. Database-backed reports with JSON, CSV, PDF and ZIP exports.

Roadmap item 4 already had hardening foundations in code:

- optional authentication / RBAC
- `.env` and file-backed secret support
- Nginx TLS reverse proxy profile
- database backup / restore helpers
- Docker CPU/memory limits
- internal backend network
- CI workflow and focused tests

## What this package adds

This upgrade closes the gap between "hardening code exists" and "hardening can be validated consistently".

- New **Release Readiness** Streamlit page.
- Local-readiness and hardening-readiness scores.
- Read-only preflight validator.
- Optional real HTTP regression matrix for all four approved scenarios.
- Local hardening secret preparation helper.
- Hardening configuration validator.
- Hardened HTTPS runtime smoke-test helper.
- PostgreSQL backup integrity verifier.
- SHA-256 evidence-bundle manifest.
- Expanded CI checks.
- Expanded contract/unit tests.
- Explicit original Phase 1-11 status in the README.

## Database compatibility

No Alembic migration is added. Existing databases remain at:

```text
005_twin_snapshots
```

## Files added

```text
pages/readiness.py
services/readiness_service.py
scripts/validate_local_release.py
scripts/prepare_hardening_secrets.py
scripts/validate_hardening_config.py
scripts/smoke_hardened_runtime.py
scripts/verify_backup.py
tests/test_secure_messenger_contracts.py
tests/test_report_bundle.py
tests/test_backup_verification.py
tests/test_auth_rbac.py
UPGRADE_NOTES_LOCAL_FEATURE_COMPLETE.md
```

## Files upgraded

```text
app.py
README.md
VERSION
services/report_service.py
pages/reports.py
sandbox/secure_messenger/app.py
requirements-dev.txt
.github/workflows/ci.yml
```

## Recommended validation order after copying into PyCharm

1. Keep the existing `.env` and `.git` directory.
2. Install/upgrade requirements.
3. Rebuild SecureMessenger because its Python package imports/tests were improved.
4. Confirm PostgreSQL is connected.
5. Confirm Alembic remains at `005_twin_snapshots`.
6. Run `pytest -q`.
7. Run `python scripts/validate_local_release.py`.
8. Run `python scripts/validate_local_release.py --exercise-sandbox`.
9. Run the four UI workflows from the Scenario Lab.
10. Create and verify a PostgreSQL backup.
11. Validate the local hardening profile.

University of Tartu server deployment remains deferred.
