from __future__ import annotations

from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from services.config_service import get_secret, get_setting


def _build_database_url() -> str:
    explicit = get_secret("RAI_DATABASE_URL")
    if explicit:
        return explicit

    database = get_setting("POSTGRES_DB", "rai_twin")
    user = get_setting("POSTGRES_USER", "rai_user")
    password = get_secret("POSTGRES_PASSWORD")
    host = get_setting("POSTGRES_HOST", "127.0.0.1")
    port = get_setting("POSTGRES_PORT", "5433")

    if not password:
        raise RuntimeError(
            "Missing PostgreSQL credentials. Copy .env.example to .env and set "
            "POSTGRES_PASSWORD, or provide POSTGRES_PASSWORD_FILE."
        )

    return (
        f"postgresql+psycopg://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{database}"
    )


DATABASE_URL = _build_database_url()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def initialize_database() -> None:
    """Compatibility hook. Alembic owns schema creation and migration."""
    return None


def get_database_session():
    return SessionLocal()


def database_health() -> dict:
    database = get_setting("POSTGRES_DB", "rai_twin")
    host = get_setting("POSTGRES_HOST", "127.0.0.1")
    port = get_setting("POSTGRES_PORT", "5433")
    try:
        with engine.connect() as connection:
            value = connection.execute(text("SELECT 1")).scalar()
        return {
            "connected": value == 1,
            "database": database,
            "url": f"{host}:{port}",
            "error": None,
        }
    except Exception as exc:
        return {
            "connected": False,
            "database": database,
            "url": f"{host}:{port}",
            "error": str(exc),
        }
