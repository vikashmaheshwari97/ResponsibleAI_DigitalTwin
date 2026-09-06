from pathlib import Path

from services.agent_identity_service import (
    PROTOTYPE_IDENTITY_NOTE,
    agent_identity_id,
    list_agent_identities,
)


def test_agent_registry_has_six_unique_prototype_ids():
    agents = list_agent_identities()
    assert len(agents) == 6
    ids = [item["e_identity_id"] for item in agents]
    assert len(set(ids)) == 6
    assert all(value.startswith("EE-AI-PROT-2026-") for value in ids)


def test_agent_registry_maps_to_o1_o4_operations():
    operations = {item["operation"] for item in list_agent_identities()}
    assert {"O1 · Plan", "O2 · Detect", "O3 · Remediate", "O4 · Verify"} <= operations


def test_identity_lookup_is_stable():
    assert agent_identity_id("Scenario Planner") == "EE-AI-PROT-2026-001"
    assert agent_identity_id("Verification Agent") == "EE-AI-PROT-2026-006"


def test_identity_disclaimer_does_not_claim_real_government_issuance():
    assert "not credentials actually issued" in PROTOTYPE_IDENTITY_NOTE


def test_sustainability_is_now_codecarbon_measured_not_identity_hardcoded():
    identity_source = Path("services/agent_identity_service.py").read_text(encoding="utf-8")
    sustainability_source = Path("services/sustainability_service.py").read_text(encoding="utf-8")
    assert "energy_kwh" not in identity_source
    assert "OfflineEmissionsTracker" in sustainability_source
    assert "energy_consumed" in sustainability_source
