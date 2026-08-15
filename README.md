# Responsible AI Digital Twin Platform

**Version:** `0.6.2-docs-consistency`  
**Current milestone:** Local grant/demo PoC feature-complete for Phases 1–10  
**Database schema:** Alembic `005_twin_snapshots`  
**Phase 11:** University of Tartu server deployment — deferred

A **Digital-Twin-Driven Responsible AI Platform** for controlled AI-agent validation, safe synthetic security testing, policy-governed remediation, human oversight, persistent evidence, professional analytics, and auditable before/after reporting.

> **Research scope:** local proof of concept.  
> **Safety boundary:** all implemented validation scenarios are predefined, synthetic, localhost-only, and execute only against the Docker `SecureMessenger` Digital Twin. The UI does not accept arbitrary external targets.  
> **Legal scope:** the platform demonstrates technical Responsible-AI controls and evidence; it does not itself make a legal determination of EU AI Act, GDPR, or other regulatory compliance.

---

## 1. Current Project Status

The local PoC has completed Phases **1–10** on the current development machine. Phase 10 is considered complete after the PostgreSQL backup has been verified and successfully restored into an isolated temporary database.

| Phase | Area | Local status |
|---|---|---:|
| 1 | Streamlit visual PoC | **100%** |
| 2 | Professional Digital Twin UI | **100%** |
| 3 | Real Digital Twin data model | **100%** |
| 4 | Real local LLM agents | **100%** |
| 5 | Agent orchestration | **100%** |
| 6 | Docker sandbox | **100%** |
| 7 | SecureMessenger synthetic mini-app | **100%** |
| 8 | Real controlled security testing | **100%** |
| 9 | Compliance / policy engine | **100%** |
| 10 | PostgreSQL + audit/evidence/analytics/reports | **100% locally after isolated restore validation** |
| 11 | University of Tartu server deployment | **0% — deferred** |

A fresh clone may temporarily display **Phase 10 = 99%** because `backups/restore_validation.json` is intentionally local and Git-ignored. Run:

```powershell
python scripts/validate_restore_backup.py
```

to reproduce the local restore validation and return Phase 10 to 100%.

### Roadmap status

| Roadmap item | State |
|---|---|
| Multiple controlled safe scenarios | **Complete** |
| Professional Run Analytics | **Complete** |
| Enhanced database-backed reports | **Complete** |
| Deployment hardening | **Implemented; local TLS + file-backed secrets are the remaining local hardening checks** |
| University of Tartu deployment | **Deferred** |

The core database architecture is intentionally frozen at `005_twin_snapshots`. No migration `006` is required for the current milestone.

---

## 2. What “Remaining Hardening” Means

The Release Readiness page can show:

```text
Remaining hardening · Local hardening TLS material, File-backed deployment secrets
```

These are **not missing application features**. They are local production-style security artifacts that are deliberately excluded from Git.

### 2.1 File-backed deployment secrets

The hardened Compose profile expects local files under:

```text
deploy/secrets/
├── postgres_password.txt
├── sandbox_admin_token.txt
├── admin_password_hash.txt
├── operator_password_hash.txt
└── auditor_password_hash.txt
```

Generate them with:

```powershell
python scripts/prepare_hardening_secrets.py
```

The helper:

- generates a random PostgreSQL password;
- generates a random sandbox administrator token;
- asks for Admin, Operator, and Auditor passwords;
- stores only bcrypt password hashes for the three UI roles;
- never prints the secret values; and
- writes the files only to the Git-ignored `deploy/secrets/` directory.

Do **not** commit the generated files.

### 2.2 Local hardening TLS material

The production-style local Nginx profile expects:

```text
deploy/certs/
├── server.crt
└── server.key
```

Generate a self-signed **local smoke-test** certificate:

PowerShell:

```powershell
.\scripts\generate_local_tls.ps1
```

WSL/Linux:

```bash
bash scripts/generate_local_tls.sh
```

These files are for local HTTPS testing only. A future University of Tartu deployment must use certificate management approved for the target infrastructure.

### 2.3 Finish the local hardening validation

After secrets and TLS files exist:

```powershell
python scripts/validate_hardening_config.py
```

Then start the production-style local profile:

```bash
docker compose down
docker compose -f docker-compose.prod.yml up -d --build
```

Run:

```powershell
python scripts/smoke_hardened_runtime.py
```

The smoke test checks:

- HTTPS through Nginx;
- Streamlit health;
- reverse-proxy security headers;
- production container state;
- PostgreSQL not exposed on a host port; and
- SecureMessenger not exposed on a host port.

This remains a **local hardening smoke test**, not Phase 11 deployment.

---

## 3. Synthetic SecureMessenger Dataset

The current SecureMessenger sandbox uses a small, explicit synthetic fixture set.

### Actual synthetic users

| ID | Username | Display name |
|---|---|---|
| `USR-001` | `alice` | Alice |
| `USR-002` | `bob` | Bob |
| `USR-003` | `charlie` | Charlie |

Therefore the current PoC has **3 implemented synthetic users**, not 50.

Earlier Digital Twin metadata displayed `synthetic_users=50`; version `0.6.2-docs-consistency` corrects that metadata to **3** so the UI matches the actual sandbox fixtures.

The three users are sufficient for the current authorization, authentication, input-validation, and rate-control scenarios. If future experiments require workload or scalability evaluation, add a deterministic synthetic-data generator rather than claiming uninstantiated users in the Twin metadata.

### Synthetic messages

```text
MSG-101 → Alice
MSG-204 → Bob
MSG-305 → Charlie
```

The sandbox also contains a deliberately synthetic expired token used only by the authentication-policy scenario.

No real user data is used.

---

## 4. Controlled Scenario Registry

The Scenario Lab contains four approved scenarios:

| ID | Scenario | Vulnerable profile | Secure expectation | Target |
|---|---|---:|---:|---|
| `SCN-001` | Unauthorized Private Message Access | HTTP `200` | HTTP `403` | Message API |
| `SCN-002` | Expired Authentication Token Acceptance | HTTP `200` | HTTP `401` | Authentication Service |
| `SCN-003` | Malformed Synthetic Message Payload | HTTP `201` | HTTP `422` | Message API |
| `SCN-004` | Local Request Burst Without Rate Control | final HTTP `200` | final HTTP `429` | API Gateway |

All scenario definitions come from the approved local registry. The UI does not accept a user-supplied target URL.

---

## 5. Governed Validation Workflow

Every scenario follows the same controlled lifecycle:

```text
Approved scenario registry
        ↓
Policy pre-check
        ↓
Scenario Planner
        ↓
Security Testing Agent
        ↓
Real localhost HTTP request
        ↓
Observer Agent
        ↓
Security Analyst
        ↓
Schema-validated local LLM output
or deterministic structured fallback
        ↓
Remediation Agent
        ↓
PERMIT_WITH_APPROVAL
        ↓
Explicit human approval
        ↓
Defensive sandbox-only remediation
        ↓
Verification Agent
        ↓
Exact same controlled test re-executed
        ↓
Expected secure HTTP behavior
        ↓
Policy verification
        ↓
Digital Twin snapshots
        ↓
SHA-256 audit-chain finalisation
        ↓
Persistent PostgreSQL evidence
```

Supported lifecycle states include:

```text
created
running
vulnerable
awaiting_approval
remediating
verifying
secured
validated
failed
rejected
interrupted
aborted
```

The intended remediation path is:

```text
ready → running → vulnerable → awaiting_approval
      → remediating → verifying → secured
```

An already-secure scenario may use:

```text
ready → running → validated
```

---

## 6. AI Agent Team

| Agent | Responsibility |
|---|---|
| Scenario Planner | prepares the approved controlled validation plan |
| Security Testing Agent | executes the real localhost HTTP test |
| Observer Agent | compares observed behavior with the secure expectation |
| Security Analyst | produces schema-valid security analysis using local Ollama or deterministic fallback |
| Remediation Agent | proposes defensive sandbox-only remediation |
| Verification Agent | re-runs the same controlled scenario after approved remediation |

### Local LLM behavior

The platform uses Ollama through a bounded client timeout.

The current preference logic favors locally available models such as:

```text
llama3*
llama*
qwen*
gemma*
mistral*
```

Structured Pydantic schemas constrain:

- finding severity;
- confidence;
- affected Twin component;
- remediation target;
- human-approval requirement; and
- target environment.

Even if an LLM produces an incorrect target, the control-plane scenario registry overrides the target component. Remediation is forced to:

```text
Digital Twin sandbox only
```

and always requires human approval.

If Ollama is unavailable or times out, deterministic schema-valid fallback behavior keeps the controlled workflow usable.

---

## 7. Professional UI

The Streamlit interface uses a shared research-console design system rather than page-specific styling.

Current UI characteristics include:

- consistent research-console page headers;
- compact sidebar session/Twin status;
- strong primary-button text contrast;
- neutral and readable disabled-button states;
- compact runtime service strips;
- workflow stepper;
- PASS/WARN/FAIL status chips;
- compact metric cards;
- tabbed evidence views;
- consolidated scenario details;
- no duplicated Agent State block in the Scenario Lab; and
- dedicated Agent Activity page for agent-level operations.

Main pages:

```text
Platform
├── Overview
└── Digital Twin

AI Validation
├── Security Scenario Lab
└── Agent Activity

Governance & Evidence
├── Run History
├── Run Analytics
├── Reports
├── Release Readiness
├── Compliance
└── Audit Trail
```

---

## 8. Digital Twin Model

The current Twin represents `SecureMessenger` and contains:

```text
User Client
    │
    ▼
API Gateway
   ├──────────────► Authentication Service
   │
   └──────────────► Message API
                         │
                         ▼
                   Message Database
```

Core properties:

```text
Name: SecureMessenger
Environment: Sandbox
External network: Localhost only
Synthetic users: 3
```

Component states include:

```text
healthy
testing
vulnerable
secured
```

The Digital Twin architecture is frozen for the current local milestone. Contract tests cover:

- required components;
- valid component edges;
- scenario-to-component mapping;
- component version fields;
- component status fields; and
- component descriptions.

---

## 9. Run Analytics

The **Run Analytics** page derives its values from PostgreSQL rather than Streamlit session state.

It includes:

- total runs;
- PASS;
- FAIL;
- interrupted/aborted;
- rejected;
- overall PASS rate;
- verification rate;
- policy block rate;
- average completed-run duration;
- human approvals;
- human rejections;
- human approval rate;
- per-scenario results;
- per-scenario verification rate;
- per-scenario average duration; and
- daily run trends.

Because the data is persisted, analytics remain available after Streamlit restarts.

---

## 10. Evidence Reports

The **Reports** page reconstructs a historical run from PostgreSQL.

Report content includes:

- executive run summary;
- scenario ID and objective;
- initial and verification HTTP evidence;
- structured finding;
- remediation proposal;
- human decision;
- policy decisions;
- rule-level policy evidence;
- Digital Twin before/after state;
- Twin snapshots;
- evidence timeline;
- audit events; and
- SHA-256 integrity status.

Exports include:

```text
evidence.json
timeline.csv
policy_rules.csv
audit.csv
report.pdf
manifest.json
complete ZIP evidence bundle
```

`manifest.json` records the byte size and SHA-256 digest for every exported evidence file.

---

## 11. PostgreSQL Evidence Store

Current Alembic head:

```text
005_twin_snapshots
```

Current persistent tables:

```text
simulation_runs
security_tests
findings
remediations
human_decisions
policy_decisions
agent_events
audit_events
policy_rules
policy_rule_results
twin_snapshots
alembic_version
```

Schema migrations:

```text
001_initial_schema
002_run_lifecycle
003_evidence_integrity
004_policy_registry
005_twin_snapshots
```

No additional schema migration is required for the current milestone.

### Backup

Create:

```powershell
python scripts/backup_database.py
```

Verify:

```powershell
python scripts/verify_backup.py
```

### Non-destructive restore validation

Run:

```powershell
python scripts/validate_restore_backup.py
```

The validator:

1. selects the latest `.sql.gz` backup;
2. creates a temporary PostgreSQL database;
3. restores the backup there;
4. checks Alembic `005_twin_snapshots`;
5. compares key source/restored table counts;
6. removes the temporary database; and
7. writes a local `backups/restore_validation.json` PASS marker.

The live `rai_twin` evidence database is not replaced by this validation.

---

## 12. Governance and Policy Engine

The policy registry includes:

| Rule ID | Purpose |
|---|---|
| `POL-SBX-001` | sandbox-only execution |
| `POL-DATA-001` | synthetic data only |
| `POL-NET-001` | external targets prohibited |
| `POL-DB-001` | persistent evidence store required |
| `POL-SCN-001` | approved scenario registry only |
| `POL-RBAC-001` | role-authorized governed execution |
| `POL-HUM-001` | explicit human approval before remediation |
| `POL-AUD-001` | privileged actions must be auditable |
| `POL-VER-001` | remediation must pass controlled verification |

Typical policy outcomes:

```text
Approved local validation              → PERMIT
Remediation before human approval       → PERMIT_WITH_APPROVAL
Human-approved defensive remediation    → PERMIT
External environment                    → BLOCK
Unauthorized execution role             → BLOCK
Failed verification                     → BLOCK / not secured
```

---

## 13. Authentication and RBAC

Authentication is optional during ordinary local development.

Roles:

| Role | Capability |
|---|---|
| `admin` | full platform and governance access |
| `operator` | execute scenarios and inspect evidence |
| `auditor` | read-only evidence, analytics, compliance, audit, and reports |

The production-style local Compose profile enables authentication.

Generate password material either with:

```powershell
python scripts/prepare_hardening_secrets.py
```

for the full hardened profile, or use:

```powershell
python scripts/generate_password_hash.py
```

for an optional `.env`-based local login test.

---

## 14. Evidence Integrity

Fresh audit events are persisted with:

```text
sequence_number
previous_hash
event_hash
integrity_version
```

Each run can be verified as a SHA-256 hash chain.

The evidence bundle separately contains file-level SHA-256 values in `manifest.json`.

These two mechanisms serve different purposes:

- **audit chain** → detects mutation/order problems in persisted audit events;
- **bundle manifest** → verifies exported files.

---

## 15. Architecture

```text
                              Browser
                                 │
                   local: Streamlit / prod-style: HTTPS
                                 │
                    ┌────────────▼────────────┐
                    │      Streamlit UI       │
                    │ professional RAI console│
                    └────────────┬────────────┘
                                 │
                ┌────────────────┼─────────────────┐
                │                │                 │
                ▼                ▼                 ▼
          Orchestration       Policy            RBAC
                │             Engine             Auth
                │                │
      ┌─────────┼─────────────┐  │
      ▼         ▼             ▼  ▼
   Planner   Security      Analyst / Remediation
             Tester             Agents
      │         │                  │
      └─────────┼──────────────────┘
                │
                ▼
       SecureMessenger Docker
           Digital Twin
                │
                ├───────────────► Twin State/Snapshots
                │
                ▼
           PostgreSQL
                │
        ┌───────┼─────────┐
        ▼       ▼         ▼
     History Analytics Reports
                         │
                         ▼
                 PDF / JSON / CSV / ZIP

Local LLM runtime: Ollama
Hardening proxy: Nginx
Evidence integrity: SHA-256
```

---

## 16. Project Structure

```text
ResponsibleAI_DigitalTwin/
├── .github/
│   └── workflows/
│       └── ci.yml
├── alembic/
│   └── versions/
│       ├── 001_initial_schema.py
│       ├── 002_run_lifecycle.py
│       ├── 003_evidence_integrity.py
│       ├── 004_policy_registry.py
│       └── 005_twin_snapshots.py
├── assets/
├── deploy/
│   ├── certs/
│   │   └── README.md
│   ├── nginx/
│   │   └── nginx.conf
│   └── secrets/
│       └── README.md
├── docs/
│   └── images/
├── models/
├── pages/
│   ├── overview.py
│   ├── digital_twin.py
│   ├── scenario_lab.py
│   ├── agents.py
│   ├── run_history.py
│   ├── analytics.py
│   ├── reports.py
│   ├── readiness.py
│   ├── compliance.py
│   └── audit.py
├── sandbox/
│   └── secure_messenger/
├── scripts/
│   ├── migrate_database.py
│   ├── backup_database.py
│   ├── verify_backup.py
│   ├── restore_database.py
│   ├── validate_restore_backup.py
│   ├── validate_local_release.py
│   ├── prepare_hardening_secrets.py
│   ├── generate_local_tls.ps1
│   ├── generate_local_tls.sh
│   ├── validate_hardening_config.py
│   └── smoke_hardened_runtime.py
├── services/
│   ├── agent_service.py
│   ├── analytics_service.py
│   ├── auth_service.py
│   ├── database_service.py
│   ├── evidence_service.py
│   ├── ollama_service.py
│   ├── orchestration_service.py
│   ├── policy_service.py
│   ├── readiness_service.py
│   ├── report_service.py
│   ├── scenario_registry_service.py
│   ├── twin_service.py
│   ├── ui_service.py
│   └── ...
├── tests/
├── .env.example
├── .gitignore
├── SECURITY.md
├── VERSION
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── requirements.txt
├── requirements-dev.txt
├── app.py
└── README.md
```

`SECURITY.md` remains as a conventional GitHub security/responsible-use policy. The two README files inside `deploy/certs/` and `deploy/secrets/` are intentionally retained so Git tracks those otherwise-empty local-only directories without tracking the generated secrets or private keys.

Historical `UPGRADE_NOTES_*.md`, old build-validation notes, and duplicated checklist/design-system Markdown are consolidated into this main README and can be removed.

---

# 17. Local Development Setup

## Prerequisites

- Windows 11 + PowerShell
- WSL2 Ubuntu
- Python 3.12
- Docker available through WSL
- Ollama installed locally
- Git
- OpenSSL for local TLS generation

## Python environment

```powershell
cd C:\Users\maheshwari\PycharmProjects\ResponsibleAI_DigitalTwin

python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

## Local environment file

Create once:

```powershell
Copy-Item .env.example .env
```

Configure local values:

```dotenv
POSTGRES_DB=rai_twin
POSTGRES_USER=rai_user
POSTGRES_PASSWORD=<local-password>

RAI_DATABASE_URL=postgresql+psycopg://rai_user:<local-password>@127.0.0.1:5433/rai_twin

SANDBOX_ADMIN_TOKEN=<local-sandbox-admin-token>
SANDBOX_BASE_URL=http://127.0.0.1:8001

OLLAMA_HOST=http://127.0.0.1:11434
AUTH_ENABLED=false
```

`.env` must remain Git-ignored.

## Development Docker profile

From WSL:

```bash
cd /mnt/c/Users/maheshwari/PycharmProjects/ResponsibleAI_DigitalTwin

docker compose up -d
docker compose ps
```

Expected services:

```text
rai-secure-messenger
rai-postgres
```

Do not run:

```bash
docker compose down -v
```

unless you intentionally want to remove the persistent PostgreSQL volume.

## Database migration check

```powershell
python scripts/migrate_database.py
python -m alembic current
```

Expected:

```text
005_twin_snapshots (head)
```

## Ollama

```powershell
ollama list
```

## Streamlit

```powershell
python -m streamlit run app.py
```

Open:

```text
http://localhost:8501
```

---

# 18. Automated Validation

Run:

```powershell
pytest -q
```

Then:

```powershell
python scripts/validate_local_release.py
```

Exercise all four real sandbox contracts:

```powershell
python scripts/validate_local_release.py --exercise-sandbox
```

Expected contract matrix:

```text
SCN-001    200 → 403
SCN-002    200 → 401
SCN-003    201 → 422
SCN-004    200 → 429
```

The exercise restores the sandbox profile after validation.

---

# 19. Demo Validation Sequence

Use **Reset Demo** between scenarios.

### SCN-001

```text
Before: HTTP 200 / FAIL
After:  HTTP 403 / PASS
```

### SCN-002

```text
Before: expired token → HTTP 200 / FAIL
After:  expired token → HTTP 401 / PASS
```

### SCN-003

```text
Before: malformed POST → HTTP 201 / FAIL
After:  same malformed POST → HTTP 422 / PASS
```

### SCN-004

```text
Before: localhost burst → final HTTP 200 / FAIL
After:  same burst → final HTTP 429 / PASS
```

For each remediation workflow verify:

1. vulnerability is observed;
2. structured analysis is generated;
3. remediation proposal is defensive and sandbox-only;
4. policy result is `PERMIT_WITH_APPROVAL`;
5. human approval is recorded;
6. the secure profile is applied;
7. the exact scenario is re-tested;
8. secure expectation passes;
9. Twin state changes;
10. evidence appears in Run History;
11. Analytics updates;
12. report bundle exports; and
13. audit integrity validates.

---

# 20. Local Hardening Checklist

Already implemented in code:

- [x] `.env` ignored by Git
- [x] legacy development secrets removed from tracked source
- [x] authentication/RBAC implementation
- [x] Nginx HTTPS configuration
- [x] security headers
- [x] backend network isolation
- [x] container CPU/memory limits
- [x] health checks
- [x] restart policies
- [x] PostgreSQL backup helper
- [x] backup verifier
- [x] non-destructive restore validator
- [x] GitHub Actions CI
- [x] automated scenario contracts
- [x] evidence-bundle integrity tests

Still local/generated:

- [ ] create file-backed hardening secrets
- [ ] create local smoke-test TLS certificate/key
- [ ] run `validate_hardening_config.py`
- [ ] run hardened HTTPS runtime smoke test

Commands:

```powershell
python scripts/prepare_hardening_secrets.py
.\scripts\generate_local_tls.ps1
python scripts/validate_hardening_config.py
```

Then:

```bash
docker compose down
docker compose -f docker-compose.prod.yml up -d --build
```

And:

```powershell
python scripts/smoke_hardened_runtime.py
```

---

# 21. Security and Responsible Use

The supported testing boundary is intentionally restricted to:

- local Docker SecureMessenger;
- synthetic users;
- synthetic tokens;
- synthetic messages;
- synthetic payloads;
- the predefined `SCN-001`–`SCN-004` registry;
- defensive remediation;
- explicit human approval; and
- post-remediation verification.

The UI does not accept arbitrary external targets.

Never commit:

```text
.env
database passwords
sandbox admin tokens
bcrypt password hashes
TLS private keys
deploy/secrets/* generated files
deploy/certs/server.key
deploy/certs/server.crt
backups/
```

See `SECURITY.md` for the repository-level responsible-use policy.

---

# 22. CI

`.github/workflows/ci.yml` performs:

- dependency installation;
- Python syntax compilation;
- focused Ruff correctness checks;
- pytest;
- legacy-secret scanning; and
- Docker Compose configuration validation.

Before pushing locally:

```powershell
pytest -q
git status
```

Check ignored secrets if needed:

```powershell
git check-ignore .env
```

---

# 23. Git Workflow

Stage changes:

```powershell
git add -A
git status
```

Commit:

```powershell
git commit -m "Consolidate documentation and align synthetic user metadata"
```

Push:

```powershell
git push origin main
```

---

# 24. Next Milestone

The local grant/demo PoC is feature-complete for **Phases 1–10**.

The immediate operational task is to complete the final local hardening smoke test:

```text
file-backed secrets
        +
local TLS
        +
hardening configuration validator
        +
HTTPS/RBAC/container-network smoke test
```

After that, freeze the local PoC.

The next major project milestone is:

```text
Phase 11 — University of Tartu Server Deployment
```

Phase 11 is intentionally deferred until the local hardened profile has been validated end-to-end.

---

## Author

**Vikash Chander Maheshwari**  
University of Tartu — Institute of Computer Science

---

## Research Prototype Notice

This repository is a research proof of concept. It demonstrates a Digital-Twin-Driven Responsible AI engineering workflow and controlled security validation architecture. It is not a production security product, legal compliance certification system, or authorization to test third-party systems.
