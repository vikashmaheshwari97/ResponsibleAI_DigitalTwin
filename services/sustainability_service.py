from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Callable, TypeVar
import uuid

import streamlit as st

try:
    from codecarbon import OfflineEmissionsTracker, OutputMethod
    CODECARBON_AVAILABLE = True
    CODECARBON_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - platform/import guard
    OfflineEmissionsTracker = None  # type: ignore[assignment]
    OutputMethod = None  # type: ignore[assignment]
    CODECARBON_AVAILABLE = False
    CODECARBON_IMPORT_ERROR = str(exc)


T = TypeVar("T")

MEASUREMENT_SCHEMA = "rai-codecarbon-v1"
AUDIT_CATEGORY = "Sustainability"
AUDIT_ACTION_PREFIX = "CodeCarbon measurement"

_DEFAULT_COUNTRY = "EST"
_DEFAULT_TRACKING_MODE = "machine"
_DEFAULT_MEASURE_POWER_SECS = 1.0
_DEFAULT_OUTPUT_DIR = "backups/codecarbon"


def _truthy(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def codecarbon_enabled() -> bool:
    return _truthy(os.getenv("CODECARBON_ENABLED"), True)


def codecarbon_configuration() -> dict[str, Any]:
    raw_interval = os.getenv(
        "CODECARBON_MEASURE_POWER_SECS",
        str(_DEFAULT_MEASURE_POWER_SECS),
    )
    try:
        interval = max(0.5, float(raw_interval))
    except (TypeError, ValueError):
        interval = _DEFAULT_MEASURE_POWER_SECS

    tracking_mode = os.getenv(
        "CODECARBON_TRACKING_MODE",
        _DEFAULT_TRACKING_MODE,
    ).strip().lower()
    if tracking_mode not in {"machine", "process"}:
        tracking_mode = _DEFAULT_TRACKING_MODE

    return {
        "enabled": codecarbon_enabled(),
        "available": CODECARBON_AVAILABLE,
        "country_iso_code": os.getenv(
            "CODECARBON_COUNTRY_ISO_CODE",
            _DEFAULT_COUNTRY,
        ).strip().upper(),
        "tracking_mode": tracking_mode,
        "measure_power_secs": interval,
        "output_dir": os.getenv(
            "CODECARBON_OUTPUT_DIR",
            _DEFAULT_OUTPUT_DIR,
        ).strip(),
        "import_error": CODECARBON_IMPORT_ERROR,
    }


def _safe_token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "unknown"


def _current_run_id() -> str | None:
    raw = st.session_state.get("current_run")
    if isinstance(raw, dict):
        return raw.get("run_id")
    return None


def _measurement_store() -> list[dict]:
    if "sustainability_measurements" not in st.session_state:
        st.session_state.sustainability_measurements = []
    return st.session_state.sustainability_measurements


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _read_last_csv_row(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        return rows[-1] if rows else {}
    except Exception:
        return {}


def _persist_measurement_audit(measurement: dict) -> None:
    if not measurement.get("run_id"):
        return
    try:
        from services.audit_service import add_audit_event

        add_audit_event(
            actor="CodeCarbon",
            action=f"{AUDIT_ACTION_PREFIX} · {measurement['agent']}",
            category=AUDIT_CATEGORY,
            status=(
                "Success"
                if measurement.get("measurement_status") == "measured"
                else "Warning"
            ),
            details=json.dumps(measurement, ensure_ascii=False, default=str),
        )
    except Exception:
        # Sustainability telemetry must never break the governed workflow.
        pass


def _record_measurement(measurement: dict) -> None:
    _measurement_store().append(measurement)
    _persist_measurement_audit(measurement)


def _unavailable_measurement(
    *,
    agent: str,
    operation: str,
    run_id: str | None,
    started_at: str,
    duration_s: float,
    reason: str,
) -> dict:
    config = codecarbon_configuration()
    return {
        "schema_version": MEASUREMENT_SCHEMA,
        "measurement_id": str(uuid.uuid4()),
        "run_id": run_id,
        "agent": agent,
        "operation": operation,
        "started_at": started_at,
        "duration_s": round(duration_s, 6),
        "energy_kwh": None,
        "emissions_kg": None,
        "emissions_g": None,
        "cpu_energy_kwh": None,
        "gpu_energy_kwh": None,
        "ram_energy_kwh": None,
        "country_iso_code": config["country_iso_code"],
        "tracking_mode": config["tracking_mode"],
        "measurement_source": "CodeCarbon OfflineEmissionsTracker",
        "measurement_status": "unavailable",
        "reason": reason,
    }


def measure_agent_activity(
    agent: str,
    operation: str,
    fn: Callable[..., T],
    *args,
    **kwargs,
) -> T:
    """
    Execute one agent stage while CodeCarbon measures the local compute window.

    Telemetry is best-effort: tracker failures never prevent the agent stage from
    running. Measurements are kept in Streamlit session state and mirrored into
    the existing audit evidence table as JSON details when a run_id exists.
    """
    config = codecarbon_configuration()
    run_id = _current_run_id()
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()

    if not config["enabled"]:
        result = fn(*args, **kwargs)
        measurement = _unavailable_measurement(
            agent=agent,
            operation=operation,
            run_id=run_id,
            started_at=started_at,
            duration_s=time.perf_counter() - started,
            reason="CodeCarbon tracking disabled by CODECARBON_ENABLED.",
        )
        measurement["measurement_status"] = "disabled"
        _record_measurement(measurement)
        return result

    if not CODECARBON_AVAILABLE:
        result = fn(*args, **kwargs)
        _record_measurement(
            _unavailable_measurement(
                agent=agent,
                operation=operation,
                run_id=run_id,
                started_at=started_at,
                duration_s=time.perf_counter() - started,
                reason=(
                    "CodeCarbon is not importable. "
                    f"{CODECARBON_IMPORT_ERROR or 'Install requirements.txt.'}"
                ),
            )
        )
        return result

    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = (
        f"{_safe_token(run_id or 'session')}_"
        f"{_safe_token(agent)}_{uuid.uuid4().hex[:8]}.csv"
    )
    output_path = output_dir / output_file

    tracker = None
    tracker_started = False
    tracker_error: str | None = None

    try:
        tracker = OfflineEmissionsTracker(
            project_name="ResponsibleAI_DigitalTwin",
            country_iso_code=config["country_iso_code"],
            tracking_mode=config["tracking_mode"],
            measure_power_secs=config["measure_power_secs"],
            output_dir=str(output_dir),
            output_file=output_file,
            output_methods=[OutputMethod.CSV],
            log_level="error",
            allow_multiple_runs=True,
        )
        tracker.start()
        tracker_started = True
    except Exception as exc:
        tracker_error = f"CodeCarbon tracker could not start: {exc}"

    stage_error: BaseException | None = None
    try:
        return fn(*args, **kwargs)
    except BaseException as exc:
        stage_error = exc
        raise
    finally:
        elapsed = time.perf_counter() - started

        if not tracker_started or tracker is None:
            _record_measurement(
                _unavailable_measurement(
                    agent=agent,
                    operation=operation,
                    run_id=run_id,
                    started_at=started_at,
                    duration_s=elapsed,
                    reason=tracker_error or "CodeCarbon tracker did not start.",
                )
            )
        else:
            stop_emissions_kg: float | None = None
            stop_error: str | None = None
            try:
                raw_stop = tracker.stop()
                if raw_stop is not None:
                    stop_emissions_kg = _float(raw_stop)
            except Exception as exc:
                stop_error = f"CodeCarbon tracker could not stop cleanly: {exc}"

            row = _read_last_csv_row(output_path)
            emissions_kg = (
                _float(row.get("emissions"))
                if row.get("emissions") not in {None, ""}
                else stop_emissions_kg
            )
            energy_kwh = (
                _float(row.get("energy_consumed"))
                if row.get("energy_consumed") not in {None, ""}
                else None
            )
            duration_s = (
                _float(row.get("duration"), elapsed)
                if row
                else elapsed
            )

            measurement = {
                "schema_version": MEASUREMENT_SCHEMA,
                "measurement_id": str(uuid.uuid4()),
                "run_id": run_id,
                "agent": agent,
                "operation": operation,
                "started_at": started_at,
                "duration_s": round(duration_s, 6),
                "energy_kwh": (
                    round(energy_kwh, 9)
                    if energy_kwh is not None
                    else None
                ),
                "emissions_kg": (
                    round(emissions_kg, 12)
                    if emissions_kg is not None
                    else None
                ),
                "emissions_g": (
                    round(emissions_kg * 1000.0, 9)
                    if emissions_kg is not None
                    else None
                ),
                "cpu_energy_kwh": (
                    round(_float(row.get("cpu_energy")), 9)
                    if row.get("cpu_energy") not in {None, ""}
                    else None
                ),
                "gpu_energy_kwh": (
                    round(_float(row.get("gpu_energy")), 9)
                    if row.get("gpu_energy") not in {None, ""}
                    else None
                ),
                "ram_energy_kwh": (
                    round(_float(row.get("ram_energy")), 9)
                    if row.get("ram_energy") not in {None, ""}
                    else None
                ),
                "cpu_power_w": (
                    round(_float(row.get("cpu_power")), 6)
                    if row.get("cpu_power") not in {None, ""}
                    else None
                ),
                "gpu_power_w": (
                    round(_float(row.get("gpu_power")), 6)
                    if row.get("gpu_power") not in {None, ""}
                    else None
                ),
                "ram_power_w": (
                    round(_float(row.get("ram_power")), 6)
                    if row.get("ram_power") not in {None, ""}
                    else None
                ),
                "country_name": row.get("country_name") or None,
                "country_iso_code": (
                    row.get("country_iso_code")
                    or config["country_iso_code"]
                ),
                "tracking_mode": (
                    row.get("tracking_mode")
                    or config["tracking_mode"]
                ),
                "codecarbon_version": row.get("codecarbon_version") or None,
                "measurement_source": "CodeCarbon OfflineEmissionsTracker",
                "measurement_status": (
                    "measured"
                    if energy_kwh is not None or emissions_kg is not None
                    else "unavailable"
                ),
                "reason": stop_error,
                "stage_status": (
                    "failed"
                    if stage_error is not None
                    else "completed"
                ),
                "csv_file": str(output_path),
            }
            _record_measurement(measurement)


def get_session_measurements(
    *,
    run_id: str | None = None,
) -> list[dict]:
    values = list(_measurement_store())
    if run_id is None:
        return values
    return [item for item in values if item.get("run_id") == run_id]


def summarise_measurements(measurements: list[dict]) -> dict:
    measured = [
        item
        for item in measurements
        if item.get("measurement_status") == "measured"
    ]
    energy = sum(
        _float(item.get("energy_kwh"))
        for item in measured
        if item.get("energy_kwh") is not None
    )
    emissions_kg = sum(
        _float(item.get("emissions_kg"))
        for item in measured
        if item.get("emissions_kg") is not None
    )
    duration = sum(
        _float(item.get("duration_s"))
        for item in measured
    )
    return {
        "measurement_source": "CodeCarbon OfflineEmissionsTracker",
        "measurement_status": (
            "measured"
            if measured
            else "not_measured"
        ),
        "energy_kwh": round(energy, 9),
        "emissions_kg": round(emissions_kg, 12),
        "emissions_g": round(emissions_kg * 1000.0, 9),
        "duration_s": round(duration, 6),
        "measured_stages": len(measured),
        "total_records": len(measurements),
        "country_iso_code": (
            measured[-1].get("country_iso_code")
            if measured
            else codecarbon_configuration()["country_iso_code"]
        ),
        "tracking_mode": (
            measured[-1].get("tracking_mode")
            if measured
            else codecarbon_configuration()["tracking_mode"]
        ),
    }


def session_sustainability_summary(
    *,
    run_id: str | None = None,
) -> dict:
    if run_id is None:
        run_id = _current_run_id()
    values = get_session_measurements(run_id=run_id) if run_id else get_session_measurements()
    return summarise_measurements(values)


def measurements_by_agent(
    measurements: list[dict] | None = None,
) -> dict[str, dict]:
    values = measurements if measurements is not None else get_session_measurements()
    output: dict[str, dict] = {}
    names = sorted({item.get("agent") for item in values if item.get("agent")})
    for name in names:
        rows = [item for item in values if item.get("agent") == name]
        output[name] = summarise_measurements(rows)
    return output


def persisted_measurements(run_id: str) -> list[dict]:
    """Recover CodeCarbon JSON measurements from the existing audit table."""
    try:
        from services.repository_service import list_audit_events

        events = list_audit_events(run_id=run_id, limit=2000)
    except Exception:
        return []

    measurements: list[dict] = []
    for event in reversed(events):
        if getattr(event, "category", None) != AUDIT_CATEGORY:
            continue
        if not str(getattr(event, "action", "")).startswith(AUDIT_ACTION_PREFIX):
            continue
        details = getattr(event, "details", "")
        try:
            payload = json.loads(details)
        except Exception:
            continue
        if isinstance(payload, dict) and payload.get("schema_version") == MEASUREMENT_SCHEMA:
            measurements.append(payload)
    return measurements


def persisted_sustainability_summary(run_id: str) -> dict:
    return summarise_measurements(persisted_measurements(run_id))
