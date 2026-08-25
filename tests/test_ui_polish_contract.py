from pathlib import Path

from services.ui_polish_service import research_polish_css


def test_global_polish_adds_safe_top_spacing_for_page_headers():
    """Final Experience v3 keeps deliberate top spacing and protected hero content."""
    css = research_polish_css()
    compact = css.replace(" ", "")
    assert ".block-container" in css
    assert "padding-top:2.2rem" in compact
    assert ".rai-eyebrow" in css
    assert "position:relative" in compact
    assert "stDeployButton" in css


def test_digital_twin_page_keeps_live_replay_and_fallback_modes():
    source = Path("pages/digital_twin.py").read_text(encoding="utf-8")
    assert "Live 3D Twin" in source
    assert "Evidence Replay" in source
    assert "2D Fallback & Inventory" in source
    assert "render_live_twin_3d" in source
    assert "render_twin_replay" in source


def test_three_dimensional_renderer_keeps_expected_interactions():
    """The final UX replaced Reset view with stronger presentation controls."""
    source = Path("components/twin_3d.py").read_text(encoding="utf-8")
    for expected in (
        "Auto-rotate",
        "Focus active",
        "Fit scene",
        "QuadraticBezierCurve3",
        'data-speed="1"',
        'data-speed="3"',
        'data-speed="5"',
        "pointerdown",
    ):
        assert expected in source
