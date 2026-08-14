# Responsible AI Digital Twin — Phase 10B Hotfix

This hotfix is based on the Phase 10B Governance & Evidence package.

## Fixes

1. **Security Analyst no longer stays indefinitely in `Running`.**
   - Local Ollama requests have a bounded timeout.
   - Ollama timeout/unavailability automatically uses the existing
     schema-valid deterministic fallback.
   - Non-LLM failures mark the agent as `Failed` and are surfaced in the UI.

2. **Visible orchestration progress.**
   - The validation workflow now executes inside the Streamlit status panel.
   - Planner, real HTTP test, observer, and analyst stages are displayed
     while they are actually executing.

3. **Compliance page rendering fixed.**
   - Removed conditional-expression calls that Streamlit Magic treated as
     displayable expression values.
   - No more `DeltaGenerator` internals or Streamlit method documentation.

4. **Incremental audit integrity.**
   - Each new audit event rebuilds the short SHA-256 chain for the current run.
   - Interrupted/incomplete new runs can therefore still have valid audit
     integrity.
   - Older Phase-10B runs can still use `Rebuild / Backfill Hash Chain`.

5. **No database migration changes.**
   - This hotfix does not add or remove tables.
   - If your database is already at `005_twin_snapshots`, do not recreate it.

## Run

```powershell
python -m alembic current
python -m streamlit run app.py
```

Expected Alembic revision:

`005_twin_snapshots (head)`

Reset the demo and run a new Security Scenario Lab workflow.


# Responsible AI Digital Twin — Phase 10B Governance & Evidence Hardening

This fully upgraded version adds:

- Alembic migrations (`001` through `005`)
- proper run lifecycle (`remediating`, `verifying`, `interrupted`, `aborted`)
- SHA-256 tamper-evident audit hash chains
- persistent policy rule registry and rule-level evidence
- persistent Digital Twin snapshots
- orchestration service
- database-backed Run History, Audit Trail, Compliance and Reports

## Apply database migrations

After copying this upgrade over the existing project:

```powershell
python -m pip install --upgrade -r requirements.txt
python scripts/migrate_database.py
alembic current
alembic history
```

Expected current revision:

`005_twin_snapshots`

The migration helper safely detects the existing Phase-10A database with its original eight tables, stamps it at `001_initial_schema`, then applies `002`–`005`. It also works with a fresh empty database.

## Run

```bash
docker compose up -d
docker compose ps
```

Keep Ollama running, then:

```powershell
python -m streamlit run app.py
```

Run one complete Security Scenario Lab workflow and inspect Run History, Compliance, Audit Trail, and Reports.
