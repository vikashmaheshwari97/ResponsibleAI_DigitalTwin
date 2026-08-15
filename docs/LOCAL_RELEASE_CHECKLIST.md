# Local Feature-Complete Release Checklist

Use this checklist before treating the local PoC as grant/demo feature-complete.

## Runtime

- [ ] Python virtual environment activates successfully.
- [ ] `python -m pip install -r requirements.txt` succeeds.
- [ ] Docker SecureMessenger is healthy.
- [ ] PostgreSQL is healthy.
- [ ] Ollama is reachable with at least one model, or deterministic fallback behavior is explicitly accepted for the demo.
- [ ] Alembic reports `005_twin_snapshots`.

## Controlled scenarios

- [ ] SCN-001 vulnerable HTTP 200 -> secure HTTP 403.
- [ ] SCN-002 vulnerable HTTP 200 -> secure HTTP 401.
- [ ] SCN-003 vulnerable HTTP 201 -> secure HTTP 422.
- [ ] SCN-004 vulnerable final HTTP 200 -> secure final HTTP 429.
- [ ] Each remediation requires human approval.
- [ ] Each successful remediation is re-tested.

## Evidence

- [ ] Run History reconstructs persisted runs after Streamlit restart.
- [ ] Analytics shows per-scenario metrics.
- [ ] Report page reconstructs before/after evidence.
- [ ] ZIP bundle contains `manifest.json`.
- [ ] Manifest SHA-256 values match bundled files.
- [ ] Audit hash chain is valid for fresh successful runs.

## Governance

- [ ] Approved-scenario rule passes only for SCN-001..SCN-004.
- [ ] Operator can execute scenarios.
- [ ] Auditor cannot execute scenarios.
- [ ] Human approval is required before security-changing remediation.
- [ ] External targets remain prohibited.

## Automated validation

```bash
pytest -q
python scripts/validate_local_release.py
python scripts/validate_local_release.py --exercise-sandbox
```
