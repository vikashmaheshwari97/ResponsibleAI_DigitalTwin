USERS = {
    "alice": {
        "id": "USR-001",
        "username": "alice",
        "display_name": "Alice",
        "token": "token-alice",
    },
    "bob": {
        "id": "USR-002",
        "username": "bob",
        "display_name": "Bob",
        "token": "token-bob",
    },
    "charlie": {
        "id": "USR-003",
        "username": "charlie",
        "display_name": "Charlie",
        "token": "token-charlie",
    },
}

# Deliberately synthetic and local-only. The application treats this token as
# expired metadata. It is accepted only in the intentionally vulnerable profile.
EXPIRED_TOKENS = {
    "expired-token-alice": "alice",
}

MESSAGES = {
    "MSG-101": {
        "id": "MSG-101",
        "owner": "alice",
        "content": "Synthetic private message belonging to Alice.",
    },
    "MSG-204": {
        "id": "MSG-204",
        "owner": "bob",
        "content": "Synthetic private message belonging to Bob.",
    },
    "MSG-305": {
        "id": "MSG-305",
        "owner": "charlie",
        "content": "Synthetic private message belonging to Charlie.",
    },
}
