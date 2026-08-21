from services.scenario_registry_service import get_scenario, list_scenarios


def test_nine_approved_controlled_scenarios_exist():
    scenarios = list_scenarios()
    assert [item.scenario_id for item in scenarios] == [
        "SCN-001",
        "SCN-002",
        "SCN-003",
        "SCN-004",
        "SCN-005",
        "SCN-006",
        "SCN-007",
        "SCN-008",
        "SCN-009",
    ]


def test_scenarios_have_secure_http_expectation():
    for scenario in list_scenarios():
        assert scenario.expected_status in {401, 403, 422, 429}
        assert scenario.objective
        assert scenario.verification_test


def test_rate_limit_scenario_is_local_controlled_test():
    scenario = get_scenario("SCN-004")
    assert scenario.test_kind == "rate_limit"
    assert scenario.expected_status == 429


def test_bulk_exfiltration_scenario_is_local_controlled_test():
    scenario = get_scenario("SCN-005")
    assert scenario.test_kind == "bulk_exfiltration"
    assert scenario.expected_status == 429
    assert scenario.severity.value == "critical"


def test_unauthorized_sharing_scenario_is_local_controlled_test():
    scenario = get_scenario("SCN-006")
    assert scenario.test_kind == "unauthorized_sharing"
    assert scenario.expected_status == 403


def test_government_request_scenario_is_local_controlled_test():
    scenario = get_scenario("SCN-007")
    assert scenario.test_kind == "government_request"
    assert scenario.expected_status == 403


def test_malicious_bot_scenario_is_local_controlled_test():
    scenario = get_scenario("SCN-008")
    assert scenario.test_kind == "malicious_bot"
    assert scenario.expected_status == 403


def test_feature_safety_scenario_is_local_controlled_test():
    scenario = get_scenario("SCN-009")
    assert scenario.test_kind == "feature_safety"
    assert scenario.expected_status == 403
