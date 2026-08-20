from dataclasses import asdict, dataclass, field
from typing import Dict, List, Tuple


@dataclass
class TwinComponent:
    component_id: str
    name: str
    kind: str
    status: str = "healthy"
    version: str = "1.0"
    description: str = ""


@dataclass
class DigitalTwin:
    name: str
    version: str
    environment: str
    synthetic_users: int
    external_network: str
    components: Dict[str, TwinComponent] = field(default_factory=dict)
    edges: List[Tuple[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["edges"] = [list(edge) for edge in self.edges]
        return payload


def create_default_twin() -> dict:
    # Keep this count aligned with sandbox/secure_messenger/database.py.
    # The current controlled PoC has six synthetic identities:
    # Alice, Bob, Charlie, Eve, Frank and Grace.
    twin = DigitalTwin(
        name="SecureMessenger",
        version="1.0",
        environment="Sandbox",
        synthetic_users=6,
        external_network="Localhost only",
        components={
            "client": TwinComponent(
                component_id="client",
                name="User Client",
                kind="client",
                description="Synthetic end-user client",
            ),
            "gateway": TwinComponent(
                component_id="gateway",
                name="API Gateway",
                kind="gateway",
                description="Entry point for application API traffic",
            ),
            "auth": TwinComponent(
                component_id="auth",
                name="Authentication Service",
                kind="service",
                description="Authenticates synthetic users",
            ),
            "message": TwinComponent(
                component_id="message",
                name="Message API",
                kind="service",
                description="Reads and writes private messages",
            ),
            "database": TwinComponent(
                component_id="database",
                name="Message Database",
                kind="database",
                description="Synthetic message storage",
            ),
            "data_export": TwinComponent(
                component_id="data_export",
                name="Data Export Service",
                kind="service",
                description="Handles bulk data export requests",
            ),
            "integration": TwinComponent(
                component_id="integration",
                name="Integration Service",
                kind="service",
                description="Manages third-party data sharing integrations",
            ),
            "legal": TwinComponent(
                component_id="legal",
                name="Legal Request Service",
                kind="service",
                description="Processes government and legal data requests",
            ),
            "bot_mgmt": TwinComponent(
                component_id="bot_mgmt",
                name="Bot Management Service",
                kind="service",
                description="Manages bot permissions and data access",
            ),
            "feature": TwinComponent(
                component_id="feature",
                name="Feature Service",
                kind="service",
                description="Implements new platform features with safety controls",
            ),
        },
        edges=[
            ("client", "gateway"),
            ("gateway", "auth"),
            ("gateway", "message"),
            ("message", "database"),
            ("gateway", "data_export"),
            ("data_export", "database"),
            ("gateway", "integration"),
            ("gateway", "legal"),
            ("gateway", "bot_mgmt"),
            ("gateway", "feature"),
            ("feature", "message"),
        ],
    )
    return twin.to_dict()
