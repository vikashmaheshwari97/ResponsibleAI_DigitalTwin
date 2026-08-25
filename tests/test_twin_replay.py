from services.twin_replay_service import (
    build_demo_replay,
    build_live_frame,
    operation_states,
    replay_json,
)
from models.twin_models import create_default_twin


def _status(operations, operation_id):
    return next(item["status"] for item in operations if item["id"] == operation_id)


def test_four_operation_model_tracks_governed_phases():
    running = operation_states("running")
    assert _status(running, "O1") == "active"
    assert _status(running, "O2") == "pending"

    vulnerable = operation_states("vulnerable")
    assert _status(vulnerable, "O1") == "complete"
    assert _status(vulnerable, "O2") == "complete"
    assert _status(vulnerable, "O3") == "pending"

    remediation = operation_states("awaiting_approval")
    assert _status(remediation, "O3") == "active"

    verifying = operation_states("verifying")
    assert _status(verifying, "O3") == "complete"
    assert _status(verifying, "O4") == "active"

    secured = operation_states("secured")
    assert all(item["status"] == "complete" for item in secured)


def test_trigger_progress_exposes_real_o4_verification_checkpoint():
    operations = operation_states("verifying", "verification_started")
    assert _status(operations, "O1") == "complete"
    assert _status(operations, "O2") == "complete"
    assert _status(operations, "O3") == "complete"
    assert _status(operations, "O4") == "active"


def test_live_frame_uses_the_same_twin_state_contract():
    twin = create_default_twin()
    twin["components"]["message"]["status"] = "vulnerable"
    frame = build_live_frame(twin, "vulnerable", scenario_id="SCN-001")
    assert frame["twin"]["components"]["message"]["status"] == "vulnerable"
    assert frame["active_component"] == "message"
    assert frame["focus_operation"] == "O2"


def test_builtin_demo_is_replayable_and_finishes_secured():
    bundle = build_demo_replay()
    assert bundle["schema_version"] == "rai-twin-replay-v1"
    assert len(bundle["frames"]) >= 6
    assert bundle["frames"][0]["focus_operation"] == "O1"
    assert any(frame["focus_operation"] == "O4" for frame in bundle["frames"])
    assert bundle["frames"][-1]["phase"] == "secured"
    assert bundle["frames"][-1]["twin"]["components"]["message"]["status"] == "secured"


def test_replay_bundle_exports_as_json():
    raw = replay_json(build_demo_replay())
    assert '"schema_version": "rai-twin-replay-v1"' in raw
    assert '"frames"' in raw
