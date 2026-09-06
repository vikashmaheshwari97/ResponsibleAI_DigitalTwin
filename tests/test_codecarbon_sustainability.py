from pathlib import Path

from services.agent_identity_service import list_agent_identities
from services.sustainability_service import (
    MEASUREMENT_SCHEMA,
    codecarbon_configuration,
    summarise_measurements,
)


def test_agent_identity_registry_still_contains_six_agents():
    agents = list_agent_identities()
    assert len(agents) == 6
    assert len({item["e_identity_id"] for item in agents}) == 6


def test_sustainability_summary_aggregates_real_measurement_shape():
    rows = [
        {
            "schema_version": MEASUREMENT_SCHEMA,
            "measurement_status": "measured",
            "energy_kwh": 0.0012,
            "emissions_kg": 0.00011,
            "duration_s": 2.5,
            "country_iso_code": "EST",
            "tracking_mode": "machine",
        },
        {
            "schema_version": MEASUREMENT_SCHEMA,
            "measurement_status": "measured",
            "energy_kwh": 0.0023,
            "emissions_kg": 0.00022,
            "duration_s": 3.5,
            "country_iso_code": "EST",
            "tracking_mode": "machine",
        },
    ]
    summary = summarise_measurements(rows)
    assert summary["energy_kwh"] == 0.0035
    assert summary["emissions_kg"] == 0.00033
    assert summary["emissions_g"] == 0.33
    assert summary["duration_s"] == 6.0
    assert summary["measured_stages"] == 2


def test_default_codecarbon_configuration_uses_estonia_offline_context():
    config = codecarbon_configuration()
    assert len(config["country_iso_code"]) == 3
    assert config["tracking_mode"] in {"machine", "process"}
    assert config["measure_power_secs"] >= 0.5


def test_orchestration_measures_all_six_agent_stages():
    source = Path("services/orchestration_service.py").read_text(encoding="utf-8")
    assert source.count("measure_agent_activity(") == 6
    for agent in (
        "Scenario Planner",
        "Security Testing Agent",
        "Observer Agent",
        "Security Analyst",
        "Remediation Agent",
        "Verification Agent",
    ):
        assert agent in source


def test_ui_no_longer_describes_sustainability_as_hardcoded():
    agents = Path("pages/agents.py").read_text(encoding="utf-8")
    twin = Path("pages/digital_twin.py").read_text(encoding="utf-8")
    assert "measured by CodeCarbon" in agents
    assert "measured with CodeCarbon rather than hardcoded" in twin


def test_requirement_includes_codecarbon_v3():
    requirements = Path("requirements.txt").read_text(encoding="utf-8")
    assert "codecarbon>=3.3.0,<4.0" in requirements
