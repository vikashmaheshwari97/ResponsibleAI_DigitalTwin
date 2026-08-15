# Phase 1–10 Completion + Professional UI Upgrade

Version: `0.6.0-phases1-10-ui`

Base commit: `028f99b` (`Complete local release validation and WSL Docker hardening support`)

This is an in-place upgrade for the existing `ResponsibleAI_DigitalTwin` project.

## What this upgrade changes

### Professional application-wide UI

- Shared research-console design system.
- Redesigned sidebar identity/environment panel.
- Consistent hero headers and status chips.
- Styled native metrics, tabs, cards, buttons, alerts and tables.
- Workflow stepper on Overview and Scenario Lab.
- Reworked Overview, Digital Twin, Scenario Lab, Agent Activity, Analytics, Run History, Reports, Compliance, Audit Trail and Release Readiness pages.

### Phase 2

Professional Digital Twin UI is considered complete for the local PoC after this upgrade.

### Phase 3

The core Digital Twin architecture remains frozen. New contract tests validate:

- required components;
- valid edges;
- scenario-to-component coverage;
- component version/status/description fields.

No database schema migration is introduced.

### Phase 4

New local-LLM contract tests validate:

- deterministic model preference;
- schema-valid analysis;
- scenario-registry target locking;
- human-approval enforcement;
- sandbox-only remediation target environment.

### Phase 5

A pure workflow lifecycle contract is added and tested for:

- the governed remediation path;
- the already-secure path;
- invalid state skipping;
- terminal-state behavior.

The existing orchestration implementation is not rewritten.

### Phase 9

Policy-engine completion tests cover:

- approved local scenario = PERMIT;
- remediation without approval = PERMIT_WITH_APPROVAL;
- human-approved remediation = PERMIT;
- external environment = BLOCK;
- unauthorized execution role = BLOCK.

### Phase 10

The existing verified backup is retained. A new non-destructive restore validator:

1. restores the latest `.sql.gz` into a temporary PostgreSQL database;
2. checks Alembic `005_twin_snapshots`;
3. compares key source/restored table counts;
4. removes the temporary database;
5. writes `backups/restore_validation.json`.

The Release Readiness page keeps Phase 10 at 99% until this check passes, then shows 100%.

## Database architecture

Unchanged.

Expected Alembic head:

`005_twin_snapshots`

No migration `006` is added.

## University of Tartu deployment

Still deferred as Phase 11.
