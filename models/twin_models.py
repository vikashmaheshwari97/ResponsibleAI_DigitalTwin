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
    twin = DigitalTwin(
        name="SecureMessenger",
        version="1.0",
        environment="Sandbox",
        synthetic_users=50,
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
        },
        edges=[
            ("client", "gateway"),
            ("gateway", "auth"),
            ("gateway", "message"),
            ("message", "database"),
        ],
    )
    return twin.to_dict()
