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
    "eve": {
        "id": "USR-004",
        "username": "eve",
        "display_name": "Eve",
        "token": "token-eve",
    },
    "frank": {
        "id": "USR-005",
        "username": "frank",
        "display_name": "Frank",
        "token": "token-frank",
    },
    "grace": {
        "id": "USR-006",
        "username": "grace",
        "display_name": "Grace",
        "token": "token-grace",
    },
}

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
    "MSG-401": {
        "id": "MSG-401",
        "owner": "eve",
        "content": "Synthetic private message belonging to Eve.",
    },
    "MSG-402": {
        "id": "MSG-402",
        "owner": "eve",
        "content": "Second synthetic private message belonging to Eve.",
    },
    "MSG-501": {
        "id": "MSG-501",
        "owner": "frank",
        "content": "Synthetic private message belonging to Frank.",
    },
    "MSG-601": {
        "id": "MSG-601",
        "owner": "grace",
        "content": "Synthetic private message belonging to Grace.",
    },
}

BOTS = {
    "weather-bot": {
        "id": "BOT-001",
        "name": "weather-bot",
        "display_name": "Weather Assistant",
        "declared_purpose": "Provide weather updates to users",
        "token": "token-weather-bot",
        "permissions": ["read_location", "read_weather_preferences"],
        "status": "active",
    },
    "analytics-bot": {
        "id": "BOT-002",
        "name": "analytics-bot",
        "display_name": "Analytics Collector",
        "declared_purpose": "Collect aggregate usage statistics",
        "token": "token-analytics-bot",
        "permissions": [
            "read_location",
            "read_weather_preferences",
            "read_message_history",
            "read_user_profiles",
            "export_data",
            "read_private_information",
        ],
        "status": "active",
    },
}

INTEGRATIONS = {
    "analytics-service": {
        "id": "INT-001",
        "name": "analytics-service",
        "display_name": "Internal Analytics Service",
        "authorized": True,
        "data_scope": "aggregate_statistics",
        "token": "token-int-analytics",
    },
    "external-marketing": {
        "id": "INT-002",
        "name": "external-marketing",
        "display_name": "External Marketing Platform",
        "authorized": False,
        "data_scope": "user_profiles",
        "token": "token-int-marketing",
    },
}

GOVERNMENT_REQUESTS = {
    "GOV-REQ-001": {
        "id": "GOV-REQ-001",
        "entity": "National Security Agency",
        "request_type": "user_data_access",
        "scope": "all_user_messages",
        "legal_basis": None,
        "authorized": False,
    },
    "GOV-REQ-002": {
        "id": "GOV-REQ-002",
        "entity": "Data Protection Authority",
        "request_type": "specific_user_data",
        "scope": "messages_for_alice",
        "legal_basis": "court_order_2024_001",
        "authorized": True,
    },
}

FEATURE_CONFIGS = {
    "ai_summarization": {
        "id": "FEAT-001",
        "name": "ai_summarization",
        "display_name": "AI Message Summarization",
        "declared_scope": "public_group_messages",
        "data_access": ["read_group_messages"],
        "sends_to_external_model": True,
        "enabled": True,
    },
}
