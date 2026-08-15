from services.ui_service import global_css


def test_primary_button_text_has_explicit_high_contrast_rule():
    css = global_css()
    assert 'button[kind="primary"]:not(:disabled)' in css
    assert 'color: #ffffff !important' in css


def test_disabled_primary_button_has_neutral_readable_state():
    css = global_css()
    assert '.stButton > button:disabled' in css
    assert 'background: #e8edf4 !important' in css
    assert 'color: #64748b !important' in css
