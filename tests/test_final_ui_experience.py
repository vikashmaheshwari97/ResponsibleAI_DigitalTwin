from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_sidebar_uses_three_workspace_information_architecture():
    app = _read("app.py")
    assert '"Control Plane"' in app
    assert '"Validation Studio"' in app
    assert '"Evidence & Governance"' in app
    assert "rai-sidebar-brand-v3" in app
    assert "rai-sidebar-twin-card" in app


def test_ui_polish_contains_research_experience_v3_contract():
    css = _read("services/ui_polish_service.py")
    assert "2026.08-research-experience-v3" in css
    assert "stDeployButton" in css
    assert "rai-sidebar-role-pill" in css
    assert "rai-operation-grid" in css
    assert "rai-twin-hint-grid" in css


def test_digital_twin_custom_html_uses_safe_renderer_not_indented_markdown():
    page = _read("pages/digital_twin.py")
    assert "def _render_html" in page
    assert "_render_html(f'<div class=\"rai-operation-grid\"" in page
    assert "Four-Operation Model" in page
    assert "Control Plane · Digital Twin" in page


def test_3d_scene_has_presentation_controls_and_replay_speeds():
    component = _read("components/twin_3d.py")
    for expected in (
        "Auto-rotate",
        "Focus active",
        "Fit scene",
        "STATE LINKED",
        "auroraSpin",
        'data-speed="1"',
        'data-speed="3"',
        'data-speed="5"',
    ):
        assert expected in component


def test_3d_scene_keeps_governed_state_semantics():
    component = _read("components/twin_3d.py")
    for state in ("healthy", "testing", "vulnerable", "secured"):
        assert state in component
    assert "active_component" in component
    assert "focus_operation" in component
