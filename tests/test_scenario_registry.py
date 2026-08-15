from services.scenario_registry_service import get_scenario, list_scenarios


def test_four_approved_controlled_scenarios_exist():
    scenarios = list_scenarios()
    assert [item.scenario_id for item in scenarios] == [
        "SCN-001",
        "SCN-002",
        "SCN-003",
        "SCN-004",
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
