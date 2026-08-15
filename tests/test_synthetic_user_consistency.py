from models.twin_models import create_default_twin
from sandbox.secure_messenger.database import USERS


def test_twin_synthetic_user_count_matches_sandbox_fixture():
    twin = create_default_twin()
    assert twin["synthetic_users"] == len(USERS)
    assert set(USERS) == {"alice", "bob", "charlie"}
