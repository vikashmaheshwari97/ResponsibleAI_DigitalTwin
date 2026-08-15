from models.twin_models import create_default_twin
from services.scenario_registry_service import list_scenarios


def test_default_twin_contract_is_complete():
    twin = create_default_twin()

    assert twin["name"] == "SecureMessenger"
    assert twin["version"] == "1.0"
    assert twin["environment"] == "Sandbox"
    assert twin["external_network"] == "Localhost only"
    assert twin["synthetic_users"] > 0

    required_components = {"client", "gateway", "auth", "message", "database"}
    assert set(twin["components"]) == required_components

    component_names = {item["name"] for item in twin["components"].values()}
    for scenario in list_scenarios():
        assert scenario.affected_component.value in component_names

    for source, target in twin["edges"]:
        assert source in required_components
        assert target in required_components


def test_all_twin_components_have_version_status_and_description():
    twin = create_default_twin()

    for component_id, component in twin["components"].items():
        assert component["component_id"] == component_id
        assert component["version"]
        assert component["status"] == "healthy"
        assert component["description"]
