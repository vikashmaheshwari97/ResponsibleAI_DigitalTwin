from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess

from sqlalchemy import text

from services.config_service import get_bool, get_secret, get_setting
from services.database_service import database_health, engine
from services.ollama_service import get_available_models
from services.sandbox_service import get_sandbox_health
from services.scenario_registry_service import list_scenarios


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ALEMBIC_VERSION = "005_twin_snapshots"
OLD_DEVELOPMENT_SECRETS = (
    "rai_" + "dev_password",
    "rai-" + "poc-admin",
)

PROJECT_PHASES = [
    {"Phase": 1, "Area": "Streamlit visual PoC", "Progress": "100%", "State": "Complete"},
    {"Phase": 2, "Area": "Professional Digital Twin UI", "Progress": "~97%", "State": "Near-complete"},
    {"Phase": 3, "Area": "Real Digital Twin data model", "Progress": "~97%", "State": "Core model frozen for this milestone"},
    {"Phase": 4, "Area": "Real local LLM agents", "Progress": "~98%", "State": "Near-complete"},
    {"Phase": 5, "Area": "Agent orchestration", "Progress": "~99%", "State": "Near-complete"},
    {"Phase": 6, "Area": "Docker sandbox", "Progress": "100%", "State": "Complete"},
    {"Phase": 7, "Area": "SecureMessenger synthetic mini-app", "Progress": "100%", "State": "Complete"},
    {"Phase": 8, "Area": "Real controlled security tests", "Progress": "100%", "State": "4 approved scenarios"},
    {"Phase": 9, "Area": "Compliance / policy engine", "Progress": "~99%", "State": "Near-complete"},
    {"Phase": 10, "Area": "PostgreSQL + audit/evidence/analytics/reports", "Progress": "~99%", "State": "Near-complete"},
    {"Phase": 11, "Area": "University of Tartu server deployment", "Progress": "0%", "State": "Deferred"},
]


@dataclass(frozen=True)
class ReadinessCheck:
    check_id: str
    category: str
    name: str
    status: str
    detail: str
    local_required: bool = False
    hardening_required: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _check(
    check_id: str,
    category: str,
    name: str,
    status: str,
    detail: str,
    *,
    local_required: bool = False,
    hardening_required: bool = False,
) -> ReadinessCheck:
    return ReadinessCheck(
        check_id=check_id,
        category=category,
        name=name,
        status=status,
        detail=detail,
        local_required=local_required,
        hardening_required=hardening_required,
    )


def _alembic_version() -> tuple[str | None, str | None]:
    try:
        with engine.connect() as connection:
            value = connection.execute(
                text("SELECT version_num FROM alembic_version LIMIT 1")
            ).scalar()
        return (str(value) if value else None, None)
    except Exception as exc:
        return (None, str(exc))


def _tracked_env_status() -> tuple[bool | None, str]:
    git = shutil.which("git")
    if not git or not (PROJECT_ROOT / ".git").exists():
        return None, "Git metadata is unavailable in this runtime."

    result = subprocess.run(
        [git, "ls-files", "--error-unmatch", ".env"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode == 0:
        return True, ".env is tracked by Git and must be removed from version control."
    return False, ".env is not tracked by Git."


def _source_secret_scan() -> list[str]:
    files: list[Path] = []
    roots = [
        PROJECT_ROOT / "services",
        PROJECT_ROOT / "sandbox",
        PROJECT_ROOT / "scripts",
        PROJECT_ROOT / "pages",
        PROJECT_ROOT / "alembic",
    ]
    for root in roots:
        if root.exists():
            files.extend(path for path in root.rglob("*") if path.is_file())

    for name in (
        "docker-compose.yml",
        "docker-compose.prod.yml",
        "alembic.ini",
        ".env.example",
    ):
        path = PROJECT_ROOT / name
        if path.exists():
            files.append(path)

    matches: list[str] = []
    for path in files:
        if path.suffix.lower() not in {
            ".py",
            ".yml",
            ".yaml",
            ".ini",
            ".toml",
            ".txt",
            ".example",
        } and path.name != ".env.example":
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for secret in OLD_DEVELOPMENT_SECRETS:
            if secret in content:
                matches.append(str(path.relative_to(PROJECT_ROOT)))
                break
    return sorted(set(matches))


def _secret_file_status(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, f"Missing: {path.relative_to(PROJECT_ROOT)}"
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        return False, f"Cannot read {path.relative_to(PROJECT_ROOT)}: {exc}"
    if not value:
        return False, f"Empty: {path.relative_to(PROJECT_ROOT)}"
    return True, f"Configured: {path.relative_to(PROJECT_ROOT)}"


def _latest_backup() -> tuple[Path | None, float | None]:
    backup_dir = Path(get_setting("BACKUP_DIR", "backups") or "backups")
    if not backup_dir.is_absolute():
        backup_dir = PROJECT_ROOT / backup_dir
    if not backup_dir.exists():
        return None, None
    backups = sorted(
        backup_dir.glob("*.sql.gz"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not backups:
        return None, None
    latest = backups[0]
    age_hours = (
        datetime.now(timezone.utc).timestamp() - latest.stat().st_mtime
    ) / 3600.0
    return latest, max(0.0, age_hours)


def _static_prod_hardening() -> dict[str, bool]:
    compose = PROJECT_ROOT / "docker-compose.prod.yml"
    nginx = PROJECT_ROOT / "deploy" / "nginx" / "nginx.conf"
    compose_text = compose.read_text(encoding="utf-8") if compose.exists() else ""
    nginx_text = nginx.read_text(encoding="utf-8") if nginx.exists() else ""
    return {
        "compose_exists": compose.exists(),
        "nginx_exists": nginx.exists(),
        "internal_network": "internal: true" in compose_text,
        "resource_limits": "mem_limit:" in compose_text and "cpus:" in compose_text,
        "restart_policy": "restart: unless-stopped" in compose_text,
        "https_listener": "listen 443 ssl" in nginx_text,
        "security_headers": (
            "X-Content-Type-Options" in nginx_text
            and "X-Frame-Options" in nginx_text
            and "Referrer-Policy" in nginx_text
        ),
    }


def collect_readiness_checks() -> list[ReadinessCheck]:
    checks: list[ReadinessCheck] = []

    env_file = PROJECT_ROOT / ".env"
    checks.append(
        _check(
            "CFG-ENV",
            "Configuration",
            "Local .env configuration",
            "PASS" if env_file.exists() else "FAIL",
            ".env exists and remains local."
            if env_file.exists()
            else "Create .env from .env.example before running the local platform.",
            local_required=True,
        )
    )

    tracked, tracked_detail = _tracked_env_status()
    checks.append(
        _check(
            "CFG-GIT-ENV",
            "Configuration",
            "Secret file excluded from Git",
            "WARN" if tracked is None else ("FAIL" if tracked else "PASS"),
            tracked_detail,
            local_required=tracked is not None,
            hardening_required=tracked is not None,
        )
    )

    source_matches = _source_secret_scan()
    checks.append(
        _check(
            "CFG-SECRET-SCAN",
            "Configuration",
            "No legacy development secrets in source",
            "FAIL" if source_matches else "PASS",
            (
                "Legacy secret text detected in: " + ", ".join(source_matches)
                if source_matches
                else "No known legacy development secret values were found in source/config files."
            ),
            local_required=True,
            hardening_required=True,
        )
    )

    db = database_health()
    checks.append(
        _check(
            "DB-CONNECTION",
            "Evidence Store",
            "PostgreSQL connectivity",
            "PASS" if db.get("connected") else "FAIL",
            (
                f"Connected to {db.get('database')} at {db.get('url')}."
                if db.get("connected")
                else f"PostgreSQL unavailable: {db.get('error')}"
            ),
            local_required=True,
            hardening_required=True,
        )
    )

    if db.get("connected"):
        version, error = _alembic_version()
        version_ok = version == EXPECTED_ALEMBIC_VERSION
        checks.append(
            _check(
                "DB-ALEMBIC",
                "Evidence Store",
                "Alembic schema version",
                "PASS" if version_ok else "FAIL",
                (
                    f"Database is at {version}."
                    if version_ok
                    else f"Expected {EXPECTED_ALEMBIC_VERSION}; found {version or error or 'unknown'}."
                ),
                local_required=True,
                hardening_required=True,
            )
        )
    else:
        checks.append(
            _check(
                "DB-ALEMBIC",
                "Evidence Store",
                "Alembic schema version",
                "FAIL",
                "Cannot verify schema version while PostgreSQL is offline.",
                local_required=True,
                hardening_required=True,
            )
        )

    sandbox = get_sandbox_health()
    checks.append(
        _check(
            "SBX-HEALTH",
            "Controlled Sandbox",
            "SecureMessenger health",
            "PASS" if sandbox.get("available") else "FAIL",
            (
                f"SecureMessenger {sandbox.get('version')} is online in "
                f"{sandbox.get('security_profile')} profile."
                if sandbox.get("available")
                else f"SecureMessenger unavailable: {sandbox.get('error')}"
            ),
            local_required=True,
            hardening_required=True,
        )
    )

    scenarios = list_scenarios()
    scenario_ids = [scenario.scenario_id for scenario in scenarios]
    scenario_ok = scenario_ids == ["SCN-001", "SCN-002", "SCN-003", "SCN-004"]
    checks.append(
        _check(
            "SCN-REGISTRY",
            "Controlled Scenarios",
            "Approved scenario registry",
            "PASS" if scenario_ok else "FAIL",
            f"Approved scenarios: {', '.join(scenario_ids) or 'none'}.",
            local_required=True,
            hardening_required=True,
        )
    )

    ollama = get_available_models()
    if ollama.get("connected") and ollama.get("models"):
        ollama_status = "PASS"
        ollama_detail = f"Ollama online with {len(ollama['models'])} local model(s)."
    elif ollama.get("connected"):
        ollama_status = "WARN"
        ollama_detail = "Ollama is reachable but no local models are available."
    else:
        ollama_status = "WARN"
        ollama_detail = (
            "Ollama is offline; deterministic schema-valid fallback remains available. "
            f"Detail: {ollama.get('error')}"
        )
    checks.append(
        _check(
            "LLM-OLLAMA",
            "Local AI Runtime",
            "Ollama model availability",
            ollama_status,
            ollama_detail,
        )
    )

    auth_enabled = get_bool("AUTH_ENABLED", False)
    if auth_enabled:
        configured_roles = []
        missing_roles = []
        for role, prefix in (
            ("admin", "RAI_ADMIN"),
            ("operator", "RAI_OPERATOR"),
            ("auditor", "RAI_AUDITOR"),
        ):
            try:
                username = get_setting(f"{prefix}_USERNAME")
                password_hash = get_secret(f"{prefix}_PASSWORD_HASH")
            except Exception:
                username = None
                password_hash = None
            if username and password_hash:
                configured_roles.append(role)
            else:
                missing_roles.append(role)
        auth_status = "PASS" if not missing_roles else "FAIL"
        auth_detail = (
            f"Authentication enabled for roles: {', '.join(configured_roles)}."
            if not missing_roles
            else f"Authentication enabled but missing configuration for: {', '.join(missing_roles)}."
        )
    else:
        auth_status = "WARN"
        auth_detail = (
            "AUTH_ENABLED=false for local development. The hardened Compose profile forces authentication on."
        )
    checks.append(
        _check(
            "AUTH-RBAC",
            "Access Control",
            "Authentication / RBAC",
            auth_status,
            auth_detail,
        )
    )

    static = _static_prod_hardening()
    checks.extend(
        [
            _check(
                "HARD-COMPOSE",
                "Hardening",
                "Production-style Compose profile",
                "PASS" if static["compose_exists"] else "FAIL",
                "docker-compose.prod.yml is present."
                if static["compose_exists"]
                else "docker-compose.prod.yml is missing.",
                hardening_required=True,
            ),
            _check(
                "HARD-NETWORK",
                "Hardening",
                "Backend network isolation",
                "PASS" if static["internal_network"] else "FAIL",
                "The production backend network is internal-only."
                if static["internal_network"]
                else "Internal backend network isolation is not configured.",
                hardening_required=True,
            ),
            _check(
                "HARD-RESOURCES",
                "Hardening",
                "Container limits and supervision",
                "PASS"
                if static["resource_limits"] and static["restart_policy"]
                else "FAIL",
                "CPU/memory limits and restart policies are configured."
                if static["resource_limits"] and static["restart_policy"]
                else "Container limits or restart policies are incomplete.",
                hardening_required=True,
            ),
            _check(
                "HARD-HTTPS-CONFIG",
                "Hardening",
                "Nginx HTTPS and security headers",
                "PASS"
                if static["nginx_exists"]
                and static["https_listener"]
                and static["security_headers"]
                else "FAIL",
                "Nginx TLS termination and baseline security headers are configured."
                if static["nginx_exists"]
                and static["https_listener"]
                and static["security_headers"]
                else "Nginx HTTPS configuration is incomplete.",
                hardening_required=True,
            ),
        ]
    )

    cert_file = PROJECT_ROOT / "deploy" / "certs" / "server.crt"
    key_file = PROJECT_ROOT / "deploy" / "certs" / "server.key"
    tls_ready = cert_file.exists() and key_file.exists()
    checks.append(
        _check(
            "HARD-TLS-MATERIAL",
            "Hardening",
            "Local hardening TLS material",
            "PASS" if tls_ready else "FAIL",
            "Local smoke-test certificate and key are present."
            if tls_ready
            else "Generate local smoke-test TLS files before validating the hardened profile.",
            hardening_required=True,
        )
    )

    secret_dir = PROJECT_ROOT / "deploy" / "secrets"
    secret_names = [
        "postgres_password.txt",
        "sandbox_admin_token.txt",
        "admin_password_hash.txt",
        "operator_password_hash.txt",
        "auditor_password_hash.txt",
    ]
    secret_results = [_secret_file_status(secret_dir / name) for name in secret_names]
    secret_ok = all(ok for ok, _ in secret_results)
    checks.append(
        _check(
            "HARD-SECRET-FILES",
            "Hardening",
            "File-backed deployment secrets",
            "PASS" if secret_ok else "FAIL",
            (
                "All production-style local secret files are configured."
                if secret_ok
                else "; ".join(detail for ok, detail in secret_results if not ok)
            ),
            hardening_required=True,
        )
    )

    latest_backup, age_hours = _latest_backup()
    if latest_backup is None:
        backup_status = "FAIL"
        backup_detail = "No PostgreSQL .sql.gz backup has been created yet."
    else:
        backup_status = "PASS"
        backup_detail = (
            f"Latest backup: {latest_backup.name} ({age_hours:.1f} hours old)."
        )
    checks.append(
        _check(
            "OPS-BACKUP",
            "Operations",
            "Database backup evidence",
            backup_status,
            backup_detail,
            hardening_required=True,
        )
    )

    ci = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
    tests_dir = PROJECT_ROOT / "tests"
    tests = list(tests_dir.glob("test_*.py")) if tests_dir.exists() else []
    checks.append(
        _check(
            "QA-CI",
            "Quality",
            "CI workflow",
            "PASS" if ci.exists() else "FAIL",
            ".github/workflows/ci.yml is present."
            if ci.exists()
            else "GitHub Actions CI workflow is missing.",
            local_required=True,
            hardening_required=True,
        )
    )
    checks.append(
        _check(
            "QA-TESTS",
            "Quality",
            "Automated test suite",
            "PASS" if len(tests) >= 3 else "WARN",
            f"Detected {len(tests)} test module(s).",
            local_required=True,
            hardening_required=True,
        )
    )

    return checks


def _score(checks: list[ReadinessCheck], scope: str) -> tuple[float, list[str]]:
    if scope not in {"local", "hardening"}:
        raise ValueError(f"Unsupported readiness scope: {scope}")

    selected = [
        item
        for item in checks
        if (item.local_required if scope == "local" else item.hardening_required)
    ]
    if not selected:
        return 100.0, []

    points = 0.0
    blockers: list[str] = []
    for item in selected:
        if item.status == "PASS":
            points += 1.0
        elif item.status == "WARN":
            points += 0.5
        else:
            blockers.append(item.name)

    return round((points / len(selected)) * 100.0, 1), blockers


def readiness_snapshot() -> dict:
    checks = collect_readiness_checks()
    local_score, local_blockers = _score(checks, "local")
    hardening_score, hardening_blockers = _score(checks, "hardening")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "expected_alembic_version": EXPECTED_ALEMBIC_VERSION,
        "local_score": local_score,
        "hardening_score": hardening_score,
        "local_blockers": local_blockers,
        "hardening_blockers": hardening_blockers,
        "phase_status": PROJECT_PHASES,
        "checks": [item.to_dict() for item in checks],
    }
