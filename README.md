# Responsible AI Digital Twin Platform

A **Digital-Twin-Driven Responsible AI Platform** for controlled AI-agent validation, synthetic security testing, policy-governed remediation, human oversight, persistent evidence, interactive Digital Twin visualisation, and auditable before/after reporting.

The platform combines a Streamlit research interface, a Docker-based `SecureMessenger` sandbox, local AI agents powered by Ollama, PostgreSQL-backed evidence storage, policy enforcement, role-based access control, and an interactive 3D Digital Twin with historical replay.

> **Research scope:** research proof of concept.  
> **Safety boundary:** validation scenarios are predefined, synthetic, and restricted to the local `SecureMessenger` Digital Twin. The platform does not accept arbitrary external targets.  
> **Legal scope:** the platform demonstrates technical Responsible-AI controls and evidence. It does not provide legal certification or determine compliance with the EU AI Act, GDPR, or other regulation.

---

## Key Capabilities

- Controlled AI-agent validation in a local Digital Twin
- Synthetic security and privacy scenarios
- Policy-governed execution and remediation
- Explicit human approval before security-changing actions
- Local LLM-assisted analysis and remediation using Ollama
- Deterministic structured fallback when the LLM is unavailable
- Four-role authentication and RBAC
- Partner-facing read-only access
- Interactive Three.js/WebGL Digital Twin
- O1–O4 lifecycle visualisation
- Historical Digital Twin replay at `1×`, `3×`, and `5×`
- PostgreSQL-backed run history and evidence
- Persistent Twin snapshots and agent events
- Run analytics and evidence reports
- SHA-256 audit-chain integrity
- Docker-based sandbox isolation
- Production-style Nginx/TLS hardening profile

---

## System Overview

```text
                              Browser
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Streamlit Research UI   │
                    │ Auth + RBAC + 3D Twin   │
                    └────────────┬────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          ▼                      ▼                      ▼
    Orchestration             Policy                  RBAC
          │                    Engine                  Auth
          │
   ┌──────┼──────────────────────────────┐
   ▼      ▼                              ▼
Planner  Security Tester        Analyst / Remediation
          │                              Agents
          └───────────────┬──────────────┘
                          ▼
                 SecureMessenger Docker
                          │
                          ▼
                    Digital Twin
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
       Live 3D State             Twin Snapshots
                                       │
                                       ▼
                                  PostgreSQL
                                       │
                     ┌─────────────────┼─────────────────┐
                     ▼                 ▼                 ▼
                  History          Analytics          Reports
                     │
                     ▼
             Historical 3D Replay
             1× / 3× / 5× playback
```

**Local AI runtime:** Ollama  
**Evidence store:** PostgreSQL  
**Sandbox:** Docker `SecureMessenger`  
**Hardening proxy:** Nginx  
**Evidence integrity:** SHA-256

---

## Controlled Validation Workflow

Every governed scenario follows the same high-level lifecycle:

```text
Approved scenario
        ↓
Policy pre-check
        ↓
Scenario Planner
        ↓
Security Testing Agent
        ↓
Observer + Security Analyst
        ↓
Finding
        ↓
Remediation Agent
        ↓
Human approval
        ↓
Defensive sandbox remediation
        ↓
Verification Agent
        ↓
Secure re-test
        ↓
Digital Twin snapshots
        ↓
PostgreSQL evidence + audit chain
```

For reviewer-facing visualisation, the workflow is grouped into four macro operations:

```text
O1 · Plan
O2 · Detect
O3 · Remediate
O4 · Verify
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

---

## Controlled Scenario Registry

The Scenario Lab contains nine predefined synthetic scenarios:

| ID | Scenario | Secure expectation | Target component |
|---|---|---:|---|
| `SCN-001` | Unauthorized Private Message Access | HTTP `403` | Message API |
| `SCN-002` | Expired Authentication Token Acceptance | HTTP `401` | Authentication Service |
| `SCN-003` | Malformed Synthetic Message Payload | HTTP `422` | Message API |
| `SCN-004` | Local Request Burst Without Rate Control | HTTP `429` | API Gateway |
| `SCN-005` | Bulk User-Data Exfiltration | HTTP `429` | Data Export Service |
| `SCN-006` | Unauthorized Third-Party Data Sharing | HTTP `403` | Integration Service |
| `SCN-007` | Government Data Request | HTTP `403` | Legal Request Service |
| `SCN-008` | Malicious / Misbehaving Bot | HTTP `403` | Bot Management Service |
| `SCN-009` | New Feature Safety Testing | HTTP `403` | Feature Service |

The first four scenarios form the core automated release-contract matrix. The remaining scenarios are integrated into the local scenario registry, sandbox, Twin mapping, and governed workflow for further validation and experimentation.

All scenarios are restricted to synthetic localhost execution.

---

## Synthetic SecureMessenger Environment

The controlled sandbox contains six synthetic identities:

| ID | Username | Display name |
|---|---|---|
| `USR-001` | `alice` | Alice |
| `USR-002` | `bob` | Bob |
| `USR-003` | `charlie` | Charlie |
| `USR-004` | `eve` | Eve |
| `USR-005` | `frank` | Frank |
| `USR-006` | `grace` | Grace |

Synthetic messages include:

```text
MSG-101 → Alice
MSG-204 → Bob
MSG-305 → Charlie
MSG-401 → Eve
MSG-402 → Eve
MSG-501 → Frank
MSG-601 → Grace
```

The sandbox also contains synthetic bot, integration, feature, government-request, and token fixtures used by the controlled scenarios.

No real user data is used.

---

## AI Agent Team

| Agent | Responsibility |
|---|---|
| Scenario Planner | prepares the approved controlled validation plan |
| Security Testing Agent | executes the localhost HTTP validation |
| Observer Agent | compares observed behaviour with the secure expectation |
| Security Analyst | produces schema-valid analysis using Ollama or deterministic fallback |
| Remediation Agent | proposes defensive sandbox-only remediation |
| Verification Agent | re-runs the controlled scenario after approved remediation |

### Local LLM behaviour

The platform uses Ollama with structured Pydantic output schemas.

Preferred local model families include:

```text
llama3*
llama*
qwen*
gemma*
mistral*
```

The scenario registry remains the control-plane source of truth for the affected Twin component and target environment.

All remediation is restricted to:

```text
Digital Twin sandbox only
```

and requires explicit human approval.

If Ollama is unavailable or times out, deterministic schema-valid fallback behaviour keeps the governed workflow usable.

---

## Authentication and Role-Based Access Control

The platform includes a dedicated login interface with:

- bcrypt password verification;
- session timeout;
- login/logout audit events;
- role-aware navigation; and
- controlled read-only partner access.

Four roles are supported:

| Role | Intended user | Main capability |
|---|---|---|
| `admin` | project team / developers | full platform control |
| `operator` | simulation operator | execute controlled scenarios and inspect evidence |
| `auditor` | governance/evidence reviewer | read-only governance, analytics, reports, and audit |
| `partner` | external research/project partner | controlled read-only preview |

### Role access matrix

| Area | Admin | Operator | Auditor | Partner |
|---|---:|---:|---:|---:|
| Overview | ✅ | ✅ | ✅ | ✅ |
| Digital Twin | ✅ | ✅ | ✅ | ✅ |
| Security Scenario Lab | ✅ | ✅ | ❌ | ❌ |
| Agent Activity | ✅ | ✅ | ❌ | ❌ |
| Run History / Analytics / Reports | ✅ | ✅ | ✅ | ✅ |
| Release Readiness | ✅ | ✅ | ✅ | ❌ |
| Compliance | ✅ | ❌ | ✅ | ✅ |
| Audit Trail | ✅ | ❌ | ✅ | ❌ |
| Reset Demo | ✅ | ✅ | ❌ | ❌ |

Configure local accounts with:

```powershell
python scripts/configure_auth_roles.py
```

The helper stores only bcrypt password hashes in `.env`.

For the hardened local deployment profile, use:

```powershell
python scripts/prepare_hardening_secrets.py
```

Never commit plaintext passwords or local authentication secrets.

---

## Interactive 3D Digital Twin

The Digital Twin page includes a Three.js/WebGL representation driven by the same state model used by the simulation engine.

The current `SecureMessenger` Twin contains:

```text
User Client
    │
    ▼
API Gateway
   ├── Authentication Service
   ├── Message API ─────────────► Message Database
   ├── Data Export Service ─────► Message Database
   ├── Integration Service
   ├── Legal Request Service
   ├── Bot Management Service
   └── Feature Service ─────────► Message API
```

Core properties:

```text
Name: SecureMessenger
Environment: Sandbox
External network: Localhost only
Synthetic users: 6
```

Component states include:

```text
healthy
testing
vulnerable
secured
```

### 3D interactions

```text
drag         → rotate
mouse wheel  → zoom
click node   → inspect component
Auto-rotate  → presentation mode
Focus active → focus the affected component
Fit scene    → restore the full topology
```

The Digital Twin page also retains a 2D fallback and component inventory.

---

## Historical Evidence Replay

The platform stores Digital Twin snapshots and agent events in PostgreSQL.

A completed simulation can therefore be replayed without executing the live sandbox workflow again.

Replay controls include:

```text
Play / Pause
Timeline scrubbing
1×
3×
5×
```

This is useful for:

- research demonstrations;
- partner review;
- grant evaluation;
- teaching;
- reproducible inspection of previous simulations.

Replay visualisation is evidence-backed rather than a pre-rendered marketing animation.

---

## PostgreSQL Evidence Store

Current Alembic head:

```text
005_twin_snapshots
```

Persistent tables include:

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

The authentication and 3D replay functionality reuses the existing schema and does not require an additional migration.

---

## Run Analytics and Reports

The application provides PostgreSQL-backed analytics and historical reports.

### Run Analytics

Includes:

- total runs;
- PASS / FAIL counts;
- verification rate;
- policy outcomes;
- interrupted / aborted / rejected runs;
- completed-run duration;
- human approval activity;
- per-scenario results; and
- daily run trends.

### Evidence Reports

Historical reports can contain:

- run summary;
- scenario objective;
- initial and verification HTTP evidence;
- structured finding;
- remediation proposal;
- human decision;
- policy decisions;
- Twin snapshots;
- agent and audit timeline; and
- SHA-256 integrity status.

Available exports include:

```text
evidence.json
timeline.csv
policy_rules.csv
audit.csv
report.pdf
manifest.json
complete ZIP evidence bundle
```

---

## Governance and Policy Engine

The policy registry includes technical controls such as:

| Rule ID | Purpose |
|---|---|
| `POL-SBX-001` | sandbox-only execution |
| `POL-DATA-001` | synthetic data only |
| `POL-NET-001` | external targets prohibited |
| `POL-DB-001` | persistent evidence store required |
| `POL-SCN-001` | approved scenario registry only |
| `POL-RBAC-001` | role-authorised governed execution |
| `POL-HUM-001` | explicit human approval before remediation |
| `POL-AUD-001` | privileged actions must be auditable |
| `POL-VER-001` | remediation must pass controlled verification |

Typical policy outcomes:

```text
Approved local validation              → PERMIT
Remediation before human approval      → PERMIT_WITH_APPROVAL
Human-approved defensive remediation   → PERMIT
External environment                   → BLOCK
Unauthorised execution role            → BLOCK
Failed verification                    → BLOCK / not secured
```

---

## Evidence Integrity

Audit events can be protected using:

```text
sequence_number
previous_hash
event_hash
integrity_version
```

Each run can be verified as a SHA-256 hash chain.

Export bundles separately include SHA-256 values in `manifest.json`.

These mechanisms provide two complementary integrity checks:

- persisted audit-event ordering and mutation detection;
- exported evidence-file verification.

---

## User Interface

The research interface is organised into three workspaces:

```text
CONTROL PLANE
├── Overview
└── Digital Twin

VALIDATION STUDIO
├── Security Scenario Lab
└── Agent Activity

EVIDENCE & GOVERNANCE
├── Run History
├── Run Analytics
├── Reports
├── Release Readiness
├── Compliance
└── Audit Trail
```

Navigation is role-aware, so each authenticated user only sees permitted areas.

The interface includes:

- shared research-console styling;
- responsive page headers;
- role and session indicators;
- runtime health cards;
- O1–O4 workflow indicators;
- interactive 3D topology;
- status chips and metrics;
- evidence tables;
- replay controls; and
- reviewer/partner-friendly presentation modes.

---

## Project Structure

```text
ResponsibleAI_DigitalTwin/
├── .github/
│   └── workflows/
├── alembic/
│   └── versions/
├── components/
│   └── twin_3d.py
├── deploy/
│   ├── certs/
│   ├── nginx/
│   └── secrets/
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
│   ├── configure_auth_roles.py
│   ├── migrate_database.py
│   ├── backup_database.py
│   ├── verify_backup.py
│   ├── validate_restore_backup.py
│   ├── validate_local_release.py
│   ├── prepare_hardening_secrets.py
│   ├── generate_password_hash.py
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
│   ├── twin_replay_service.py
│   ├── twin_service.py
│   ├── ui_polish_service.py
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

---

## Local Development

### Prerequisites

- Windows 11 + PowerShell
- WSL2 Ubuntu
- Python 3.12
- Docker
- Ollama
- Git
- OpenSSL for local TLS generation

### Python environment

```powershell
cd C:\Users\maheshwari\PycharmProjects\ResponsibleAI_DigitalTwin

python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

### Environment configuration

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

Example:

```dotenv
POSTGRES_DB=rai_twin
POSTGRES_USER=rai_user
POSTGRES_PASSWORD=<local-password>

RAI_DATABASE_URL=postgresql+psycopg://rai_user:<local-password>@127.0.0.1:5433/rai_twin

SANDBOX_ADMIN_TOKEN=<local-sandbox-admin-token>
SANDBOX_BASE_URL=http://127.0.0.1:8001

OLLAMA_HOST=http://127.0.0.1:11434

AUTH_ENABLED=true
AUTH_SESSION_TIMEOUT_MINUTES=60

RAI_ADMIN_USERNAME=admin
RAI_ADMIN_PASSWORD_HASH=<bcrypt-hash>

RAI_OPERATOR_USERNAME=operator
RAI_OPERATOR_PASSWORD_HASH=<bcrypt-hash>

RAI_AUDITOR_USERNAME=auditor
RAI_AUDITOR_PASSWORD_HASH=<bcrypt-hash>

RAI_PARTNER_USERNAME=partner
RAI_PARTNER_PASSWORD_HASH=<bcrypt-hash>
```

`.env` must remain Git-ignored.

Configure the four accounts with:

```powershell
python scripts/configure_auth_roles.py
```

### Start Docker services

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

### Database migrations

```powershell
python scripts/migrate_database.py
python -m alembic current
```

Expected:

```text
005_twin_snapshots (head)
```

### Ollama

```powershell
ollama list
```

### Start Streamlit

```powershell
python -m streamlit run app.py
```

Open:

```text
http://localhost:8501
```

---

## Automated Validation

Run the full test suite:

```powershell
pytest -q
```

Run the local release validator:

```powershell
python scripts/validate_local_release.py
```

The core automated sandbox contract matrix is:

```text
SCN-001    200 → 403
SCN-002    200 → 401
SCN-003    201 → 422
SCN-004    200 → 429
```

Additional scenarios `SCN-005`–`SCN-009` can be exercised separately.

---

## Backup and Restore Validation

Create a PostgreSQL backup:

```powershell
python scripts/backup_database.py
```

Verify it:

```powershell
python scripts/verify_backup.py
```

Validate restoration without replacing the live database:

```powershell
python scripts/validate_restore_backup.py
```

The restore validator uses a temporary PostgreSQL database and leaves the live `rai_twin` evidence store unchanged.

---

## Local Hardening

The repository includes a production-style local hardening profile using:

- Nginx TLS termination;
- security headers;
- file-backed secrets;
- backend network isolation;
- container resource limits;
- health checks; and
- restart policies.

Generate local file-backed secrets:

```powershell
python scripts/prepare_hardening_secrets.py
```

Generate local smoke-test TLS material:

```powershell
.\scripts\generate_local_tls.ps1
```

Validate configuration:

```powershell
python scripts/validate_hardening_config.py
```

Start the hardened profile:

```bash
docker compose down
docker compose -f docker-compose.prod.yml up -d --build
```

Run the hardened runtime smoke test:

```powershell
python scripts/smoke_hardened_runtime.py
```

Generated secrets and private keys must never be committed.

---

## Security and Responsible Use

The supported testing boundary is intentionally restricted to:

- the local Docker `SecureMessenger` sandbox;
- synthetic users, messages, tokens, bots, integrations, and requests;
- predefined `SCN-001`–`SCN-009` scenarios;
- defensive remediation;
- explicit human approval; and
- controlled post-remediation verification.

The UI does not accept arbitrary external targets.

Never commit:

```text
.env
database passwords
sandbox admin tokens
plaintext UI passwords
bcrypt password hashes used as local secrets
TLS private keys
deploy/secrets/* generated files
deploy/certs/server.key
deploy/certs/server.crt
backups/
```

See `SECURITY.md` for repository-level responsible-use guidance.

---

## CI

The GitHub Actions workflow performs automated repository validation including dependency installation, syntax checks, pytest, secret scanning, and Docker Compose configuration validation.

Before pushing locally:

```powershell
pytest -q
git diff --check
git status
```

Check ignored local secrets when needed:

```powershell
git check-ignore .env
```

---

## Author

**Vikash Chander Maheshwari**  
University of Tartu — Institute of Computer Science

---

## Research Prototype Notice

This repository is a research proof of concept for Digital-Twin-Driven Responsible AI engineering and controlled security validation.

It is not:

- a production security product;
- a legal compliance certification system; or
- authorisation to test third-party systems.
