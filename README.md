# Responsible AI Digital Twin Platform

A **Digital-Twin-Driven Responsible AI Platform** for controlled AI-agent validation, safe sandbox testing, policy-governed remediation, human oversight, persistent evidence, professional analytics, and auditable before/after reporting.

> **Current scope:** local research prototype / PoC.  
> **Safety boundary:** all security scenarios are predefined, synthetic, localhost-only, and execute only against the Docker `SecureMessenger` Digital Twin. The UI does not accept arbitrary external targets.  
> **University of Tartu server deployment:** intentionally deferred to the final project milestone.

## What is implemented now

This version completes the local-code work for Roadmap items **1–4**:

1. **Multiple controlled safe scenarios**
2. **Professional Run Analytics**
3. **Enhanced Database-Backed Reports**
4. **Deployment Hardening foundations**

The remaining major milestone is **University of Tartu server deployment**, which will be done later.

---

## Controlled Scenario Registry

The Scenario Lab now contains four approved scenarios:

| ID | Scenario | Vulnerable profile | Secure expectation | Target |
|---|---|---:|---:|---|
| `SCN-001` | Unauthorized Private Message Access | HTTP 200 | HTTP 403 | Message API |
| `SCN-002` | Expired Authentication Token Acceptance | HTTP 200 | HTTP 401 | Authentication Service |
| `SCN-003` | Malformed Synthetic Message Payload | HTTP 201 | HTTP 422 | Message API |
| `SCN-004` | Local Request Burst Without Rate Control | final HTTP 200 | final HTTP 429 | API Gateway |

Each scenario follows the same governed workflow:

```text
Approved scenario registry
        ↓
Policy pre-check
        ↓
Scenario Planner
        ↓
Real local HTTP test against Docker SecureMessenger
        ↓
Observer
        ↓
Schema-validated Security Analyst output
        ↓
Defensive Remediation Agent proposal
        ↓
PERMIT_WITH_APPROVAL
        ↓
Explicit human approval
        ↓
Secure sandbox profile applied
        ↓
Exact same scenario re-executed
        ↓
Expected secure HTTP behavior
        ↓
Policy verification + Twin snapshots + hash-chain finalization
        ↓
Persistent PostgreSQL evidence
```

The local sandbox contains deliberately synthetic behavior for each scenario. Resetting the demo restores the vulnerable profile; approved remediation switches the sandbox to secure profile `1.1`.

---

## Professional Run Analytics

A new **Run Analytics** page derives metrics from PostgreSQL rather than Streamlit session state.

It includes:

- total run count
- PASS count
- FAIL count
- interrupted/aborted count
- rejected count
- verification rate
- policy block rate
- average completed-run duration
- human approvals
- human rejections
- human approval rate
- per-scenario PASS/FAIL/interrupted breakdown
- per-scenario verification rate
- per-scenario average duration
- daily run trend

Analytics remain available after Streamlit restarts because they are reconstructed from the persistent evidence store.

---

## Enhanced Reports

The **Reports** page reconstructs a historical run from PostgreSQL and includes:

- executive run summary
- scenario ID and objective
- before/after HTTP evidence
- structured finding
- remediation proposal
- human-oversight decisions
- policy decisions
- rule-level policy evidence
- Digital Twin before/after state
- Twin snapshots
- evidence timeline
- audit events
- SHA-256 evidence-integrity status

Exports:

- JSON evidence file
- timeline CSV
- policy-rule CSV
- audit CSV
- PDF evidence report
- complete ZIP evidence bundle containing JSON + CSV + PDF

---

## Deployment Hardening Foundations

The project now includes code/configuration for the deployment-hardening roadmap while keeping local development simple.

### Secrets management

Local development uses a git-ignored `.env` file. The code also supports file-backed secrets through `<NAME>_FILE`, which is used by the hardened Compose profile.

Never commit `.env`, passwords, access tokens, password hashes, TLS private keys, or deployment secret files.

### Authentication and RBAC

Authentication is optional for local development and enabled in the production-style Compose profile.

Roles:

| Role | Access |
|---|---|
| `admin` | full access |
| `operator` | execute scenarios, view evidence, analytics and reports |
| `auditor` | read-only evidence, analytics, compliance, audit and reports |

Generate bcrypt hashes with:

```bash
python scripts/generate_password_hash.py
```

For local development set `AUTH_ENABLED=true` and place hashes in `.env` if you want to test the login gate.

### Reverse proxy and HTTPS

`docker-compose.prod.yml` includes Nginx with TLS termination. Generate local self-signed certificates only for a smoke test:

PowerShell:

```powershell
./scripts/generate_local_tls.ps1
```

WSL/Linux:

```bash
bash scripts/generate_local_tls.sh
```

Real deployments must use certificates issued/managed according to the target infrastructure policy.

### Database backups

Create a compressed PostgreSQL backup:

```bash
python scripts/backup_database.py
```

Restore only after an explicit confirmation:

```bash
python scripts/restore_database.py backups/<backup>.sql.gz --confirm RESTORE
python scripts/migrate_database.py
```

### Docker resource limits and service supervision

Development and production-style Compose files include resource limits, health checks and `restart: unless-stopped`.

### Network isolation

The hardened Compose profile separates:

- `frontend` network: Nginx ↔ Streamlit
- internal `backend` network: Streamlit ↔ PostgreSQL ↔ SecureMessenger

PostgreSQL and SecureMessenger do not publish host ports in the production-style profile.

### CI/tests

`.github/workflows/ci.yml` runs:

- Python dependency installation
- syntax compilation
- focused Ruff correctness checks
- pytest unit tests

---

## Architecture

```text
                         Browser
                            │
                     HTTPS / Nginx
                            │
                            ▼
                     Streamlit UI
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
     Orchestrator       Policy Engine     RBAC / Auth
          │                 │
          ├────────────┐    │
          ▼            ▼    ▼
      AI Agents     Evidence Engine
          │            │
          ▼            ▼
  SecureMessenger   PostgreSQL
   Docker Sandbox       │
          │             ▼
          │          Analytics
          │             │
          └──────► Reports / PDF / CSV / JSON

Local LLM: Ollama
Digital Twin: state + topology + snapshots
Evidence integrity: SHA-256 audit chain
```

---

## Main Project Structure

```text
ResponsibleAI_DigitalTwin/
├── .github/workflows/ci.yml
├── alembic/
│   └── versions/
│       ├── 001_initial_schema.py
│       ├── 002_run_lifecycle.py
│       ├── 003_evidence_integrity.py
│       ├── 004_policy_registry.py
│       └── 005_twin_snapshots.py
├── deploy/
│   ├── certs/
│   ├── nginx/nginx.conf
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
│   ├── compliance.py
│   └── audit.py
├── sandbox/secure_messenger/
├── scripts/
│   ├── migrate_database.py
│   ├── backup_database.py
│   ├── restore_database.py
│   ├── generate_password_hash.py
│   ├── generate_local_tls.ps1
│   └── generate_local_tls.sh
├── services/
│   ├── analytics_service.py
│   ├── auth_service.py
│   ├── config_service.py
│   ├── report_service.py
│   ├── scenario_registry_service.py
│   └── ...
├── tests/
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── requirements.txt
├── requirements-dev.txt
├── app.py
└── README.md
```

---

# Local Development Setup

## 1. Python environment

Windows PowerShell:

```powershell
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 2. Environment file

If `.env` already exists from the current project, keep it.

For a new setup:

```powershell
Copy-Item .env.example .env
```

At minimum configure:

```dotenv
POSTGRES_DB=rai_twin
POSTGRES_USER=rai_user
POSTGRES_PASSWORD=<local-password>
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5433
SANDBOX_ADMIN_TOKEN=<local-admin-token>
SANDBOX_BASE_URL=http://127.0.0.1:8001
OLLAMA_HOST=http://127.0.0.1:11434
AUTH_ENABLED=false
```

Your existing database password must continue to match the password with which the current PostgreSQL volume was initialized.

## 3. Rebuild Docker SecureMessenger

The sandbox application changed to support all four controlled scenarios, so rebuild it once:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose ps
```

Do **not** use `docker compose down -v` unless you intentionally want to remove the persistent PostgreSQL volume.

Expected:

```text
rai-secure-messenger   Up (healthy)
rai-postgres           Up (healthy)
```

## 4. Database migrations

No new database schema migration is required for this roadmap package. The existing schema remains at:

```text
005_twin_snapshots (head)
```

Still run the safe migration helper:

```powershell
python scripts/migrate_database.py
python -m alembic current
```

Expected:

```text
005_twin_snapshots (head)
```

## 5. Ollama

Check:

```powershell
ollama list
```

The current PoC prefers a local model such as `llama3:latest`. If the local LLM is unavailable or exceeds the bounded timeout, schema-valid deterministic fallbacks keep the controlled workflow usable.

## 6. Start Streamlit

```powershell
python -m streamlit run app.py
```

Open:

```text
http://localhost:8501
```

---

# Validation Checklist

Use **Reset Demo** between scenarios so SecureMessenger returns to profile `1.0 / vulnerable`.

## SCN-001

Expected initial:

```text
HTTP 200 / FAIL
```

After approved remediation:

```text
HTTP 403 / PASS
```

## SCN-002

Expected initial:

```text
expired synthetic token → HTTP 200 / FAIL
```

After approved remediation:

```text
expired synthetic token → HTTP 401 / PASS
```

## SCN-003

Expected initial:

```text
malformed synthetic POST /messages → HTTP 201 / FAIL
```

After approved remediation:

```text
same malformed payload → HTTP 422 / PASS
```

## SCN-004

Expected initial:

```text
8-request localhost burst → final HTTP 200 / FAIL
```

After approved remediation:

```text
same 8-request burst → final HTTP 429 / PASS
```

After successful runs, open:

1. **Run History** — persistent evidence
2. **Run Analytics** — aggregated metrics and trends
3. **Reports** — PDF/JSON/CSV/ZIP exports
4. **Compliance** — `POL-SCN-001` and `POL-RBAC-001` plus existing governance rules
5. **Audit Trail** — evidence hash-chain verification

---

# Optional Local RBAC Test

Generate three password hashes:

```powershell
python scripts/generate_password_hash.py
```

Add them to `.env`:

```dotenv
AUTH_ENABLED=true
RAI_ADMIN_USERNAME=admin
RAI_ADMIN_PASSWORD_HASH=<bcrypt-hash>
RAI_OPERATOR_USERNAME=operator
RAI_OPERATOR_PASSWORD_HASH=<bcrypt-hash>
RAI_AUDITOR_USERNAME=auditor
RAI_AUDITOR_PASSWORD_HASH=<bcrypt-hash>
```

Restart Streamlit. The auditor role will not receive the Scenario Lab page; operator/admin can execute governed workflows.

---

# Production-Style Local Hardening Smoke Test

This is **not** the University of Tartu deployment. It is only a local validation of the hardening configuration.

1. Create deployment secret files under `deploy/secrets/`.
2. Generate local TLS material under `deploy/certs/`.
3. Ensure Ollama is reachable through `OLLAMA_HOST`.
4. Run:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Then use:

```text
https://localhost:8443
```

The self-signed certificate will produce a browser warning during local testing.

---

## Persistent Evidence Tables

The current PostgreSQL schema contains:

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

No destructive schema migration is included in this upgrade.

---

## Governance Rules

The registry includes:

| Rule ID | Purpose |
|---|---|
| `POL-SBX-001` | Sandbox-only execution |
| `POL-DATA-001` | Synthetic data only |
| `POL-NET-001` | External targets prohibited |
| `POL-DB-001` | Persistent evidence store required |
| `POL-SCN-001` | Approved scenario registry only |
| `POL-RBAC-001` | Authorized role required for governed execution |
| `POL-HUM-001` | Human approval required for remediation |
| `POL-AUD-001` | Privileged actions must be auditable |
| `POL-VER-001` | Remediation requires successful verification |

These are technical controls for the research prototype. The project does not itself establish legal compliance with the EU AI Act, GDPR, or another legal regime.

---

## Development Progress After This Package

| Area | State |
|---|---:|
| Streamlit visual PoC | 100% |
| Professional Digital Twin UI | ~95% |
| Digital Twin data model | ~95% |
| Real LLM agents | ~97% |
| Agent orchestration | ~97% |
| Docker sandbox | 100% |
| SecureMessenger synthetic mini-app | 100% |
| Controlled security tests | 100% for 4 approved scenarios |
| Policy/compliance engine | ~97% |
| PostgreSQL + audit/evidence | ~98% |
| Run Analytics | implemented |
| Enhanced Reports | implemented |
| Deployment-hardening foundations | implemented in code; deployment validation still required |
| University of Tartu server deployment | **deferred / not started** |

---

## Next Major Milestone

The next major project milestone is **University of Tartu Server Deployment**, but it is intentionally postponed until the local multi-scenario, analytics, reporting and hardening package has been validated end-to-end.

Before UT deployment, validate all four scenarios, RBAC, backups, exports, CI, and the local HTTPS production-style profile.

---

## Research Prototype Disclaimer

This repository demonstrates technical mechanisms for Responsible AI oversight, Digital Twin state management, controlled security validation, safe agent orchestration, policy-controlled remediation, persistent evidence, analytics, reporting, and auditability.

It is not a production security-testing product and must not be used to target systems without explicit authorization.
