from __future__ import annotations

from copy import deepcopy

import streamlit as st

from models.twin_models import create_default_twin
from services.scenario_registry_service import get_scenario


_COMPONENT_TO_TWIN_ID = {
    "API Gateway": "gateway",
    "Authentication Service": "auth",
    "Message API": "message",
    "Message Database": "database",
    "Data Export Service": "data_export",
    "Integration Service": "integration",
    "Legal Request Service": "legal",
    "Bot Management Service": "bot_mgmt",
    "Feature Service": "feature",
}


def default_agent_status() -> dict:
    return {
        "Scenario Planner": "Ready",
        "Security Testing Agent": "Ready",
        "Observer Agent": "Ready",
        "Security Analyst": "Ready",
        "Remediation Agent": "Ready",
        "Verification Agent": "Standby",
    }


def _defaults() -> dict:
    scenario = get_scenario("SCN-001")
    return {
        "phase": "ready",
        "simulation_count": 0,
        "twin": create_default_twin(),
        "selected_scenario_id": scenario.scenario_id,
        "selected_scenario": scenario.name,
        "scenario_objective": scenario.objective,
        "current_finding": None,
        "structured_finding": None,
        "remediation_proposal": None,
        "structured_remediation": None,
        "agent_status": default_agent_status(),
        "agent_events": [],
        "audit_log": [],
        "policy_decision": None,
        "policy_history": [],
        "current_run": None,
        "run_history": [],
        "report_ready": False,
        "ollama_model": None,
        "analyst_llm_output": None,
        "analyst_source": None,
        "remediation_llm_output": None,
        "remediation_source": None,
        "last_security_test": None,
        "verification_test": None,
        "remediation_policy_approved": False,
        "orchestration_error": None,
        "before_metrics": {
            "Security Score": 61,
            "High-Risk Findings": 1,
            "Tests Passed": 67,
            "Policy Violations": 1,
        },
        "after_metrics": {
            "Security Score": 92,
            "High-Risk Findings": 0,
            "Tests Passed": 96,
            "Policy Violations": 0,
        },
    }


def initialize_session_state() -> None:
    for key, value in _defaults().items():
        if key not in st.session_state:
            st.session_state[key] = deepcopy(value)


def select_scenario(scenario_id: str) -> None:
    scenario = get_scenario(scenario_id)
    st.session_state.selected_scenario_id = scenario.scenario_id
    st.session_state.selected_scenario = scenario.name
    st.session_state.scenario_objective = scenario.objective


def reset_demo() -> None:
    selected_model = st.session_state.get("ollama_model")
    selected_scenario_id = st.session_state.get("selected_scenario_id", "SCN-001")

    for key, value in _defaults().items():
        st.session_state[key] = deepcopy(value)

    st.session_state.ollama_model = selected_model
    select_scenario(selected_scenario_id)

    try:
        from services.sandbox_service import reset_sandbox

        reset_sandbox()
    except Exception:
        pass


def _current_component_id() -> str:
    scenario = get_scenario(st.session_state.get("selected_scenario_id", "SCN-001"))
    return _COMPONENT_TO_TWIN_ID.get(scenario.affected_component.value, "message")


def get_platform_metrics() -> dict:
    phase = st.session_state.phase
    if phase == "running":
        return {
            "security_score": 76,
            "active_agents": 4,
            "high_findings": 0,
            "tests_passed": None,
            "risk": "Analysing",
        }
    if phase in {"vulnerable", "awaiting_approval", "remediating", "verifying"}:
        return {
            "security_score": 61,
            "active_agents": 0,
            "high_findings": 1,
            "tests_passed": 67,
            "risk": "High",
        }
    if phase in {"secured", "validated"}:
        return {
            "security_score": 92,
            "active_agents": 0,
            "high_findings": 0,
            "tests_passed": 96,
            "risk": "Low",
        }
    return {
        "security_score": 76,
        "active_agents": 0,
        "high_findings": 0,
        "tests_passed": None,
        "risk": "Ready",
    }


def _set_component_status(component_id: str, status: str) -> None:
    st.session_state.twin["components"][component_id]["status"] = status


def set_running() -> None:
    st.session_state.phase = "running"
    _set_component_status(_current_component_id(), "testing")


def mark_vulnerability() -> None:
    st.session_state.phase = "vulnerable"
    component_id = _current_component_id()
    _set_component_status(component_id, "vulnerable")

    result = st.session_state.get("last_security_test") or {}
    structured = st.session_state.get("structured_finding") or {}
    scenario = get_scenario(st.session_state.selected_scenario_id)

    st.session_state.current_finding = {
        "id": f"SEC-{scenario.scenario_id[-3:]}",
        "title": structured.get("classification", scenario.classification),
        "component": structured.get(
            "affected_component", scenario.affected_component.value
        ),
        "severity": str(structured.get("severity", scenario.severity.value)).title(),
        "confidence": str(structured.get("confidence", scenario.confidence)).title(),
        "category": scenario.category,
        "description": structured.get("root_cause", scenario.root_cause),
        "evidence": (
            f"Expected HTTP {result.get('expected_status')}; observed HTTP "
            f"{result.get('observed_status')} for {result.get('resource_id')}."
        ),
    }


def mark_validated() -> None:
    st.session_state.phase = "validated"
    _set_component_status(_current_component_id(), "healthy")
    st.session_state.report_ready = True


def set_remediation_proposal() -> None:
    st.session_state.phase = "awaiting_approval"
    structured = st.session_state.get("structured_remediation") or {}
    scenario = get_scenario(st.session_state.selected_scenario_id)
    st.session_state.remediation_proposal = {
        "id": structured.get("remediation_id"),
        "component": structured.get(
            "target_component", scenario.affected_component.value
        ),
        "title": structured.get("title", scenario.remediation_title),
        "description": structured.get("proposed_change", scenario.remediation_change),
        "risk": str(structured.get("risk", "low")).title(),
        "environment": structured.get(
            "target_environment", "Digital Twin sandbox only"
        ),
        "approval_required": bool(
            structured.get("requires_human_approval", True)
        ),
    }


def reject_remediation_state() -> None:
    st.session_state.phase = "vulnerable"
    st.session_state.remediation_proposal = None
    st.session_state.structured_remediation = None
    st.session_state.remediation_policy_approved = False
    st.session_state.agent_status["Remediation Agent"] = "Ready"


def mark_remediating_state() -> None:
    st.session_state.phase = "remediating"


def mark_verifying_state() -> None:
    st.session_state.phase = "verifying"


def mark_secured() -> None:
    st.session_state.phase = "secured"
    st.session_state.twin["version"] = "1.1"
    component_id = _current_component_id()
    st.session_state.twin["components"][component_id]["version"] = "1.1"
    _set_component_status(component_id, "secured")
    st.session_state.report_ready = True


def sync_twin_from_sandbox(health: dict) -> None:
    if not health.get("available"):
        return
    version = health.get("version")
    if version:
        st.session_state.twin["version"] = version


def build_digital_twin_mermaid() -> str:
    twin = st.session_state.twin
    components = twin["components"]
    icon_map = {
        "client": "👤",
        "gateway": "🌐",
        "service": "⚙️",
        "database": "🗄️",
    }
    class_map = {
        "healthy": "healthy",
        "secured": "healthy",
        "vulnerable": "vulnerable",
        "testing": "testing",
    }
    lines = ["flowchart TB"]
    for component_id, component in components.items():
        icon = icon_map.get(component["kind"], "◼")
        status = component["status"].replace("_", " ").upper()
        label = f'{icon} {component["name"]}<br/>{status}'
        lines.append(f'    {component_id}["{label}"]')
    for source, target in twin["edges"]:
        lines.append(f"    {source} --> {target}")
    lines.extend(
        [
            "    classDef client fill:#eff6ff,stroke:#2563eb,stroke-width:2px,color:#1e3a8a;",
            "    classDef healthy fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#166534;",
            "    classDef vulnerable fill:#fee2e2,stroke:#dc2626,stroke-width:3px,color:#991b1b;",
            "    classDef testing fill:#fef3c7,stroke:#d97706,stroke-width:3px,color:#92400e;",
        ]
    )
    for component_id, component in components.items():
        css_class = (
            "client"
            if component["kind"] == "client"
            else class_map.get(component["status"], "healthy")
        )
        lines.append(f"    class {component_id} {css_class};")
    return "\n".join(lines)


def render_digital_twin() -> None:
    st.mermaid_chart(build_digital_twin_mermaid(), width="stretch")
