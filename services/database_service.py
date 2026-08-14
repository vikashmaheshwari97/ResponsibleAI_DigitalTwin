from __future__ import annotations

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


load_dotenv()


def _build_database_url() -> str:
    explicit = os.getenv("RAI_DATABASE_URL")

    if explicit:
        return explicit

    database = os.getenv("POSTGRES_DB", "rai_twin")
    user = os.getenv("POSTGRES_USER", "rai_user")
    password = os.getenv("POSTGRES_PASSWORD")

    if not password:
        raise RuntimeError(
            "Missing PostgreSQL credentials. Copy .env.example to .env "
            "and set POSTGRES_PASSWORD / RAI_DATABASE_URL."
        )

    return (
        f"postgresql+psycopg://{user}:{password}"
        f"@127.0.0.1:5433/{database}"
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
    """Compatibility hook. Schema creation/upgrades are managed by Alembic."""
    return None


def get_database_session():
    return SessionLocal()


def database_health() -> dict:
    database = os.getenv(
        "POSTGRES_DB",
        "rai_twin",
    )

    try:
        with engine.connect() as connection:
            value = connection.execute(
                text("SELECT 1")
            ).scalar()

        return {
            "connected": value == 1,
            "database": database,
            "url": "127.0.0.1:5433",
            "error": None,
        }

    except Exception as exc:
        return {
            "connected": False,
            "database": database,
            "url": "127.0.0.1:5433",
            "error": str(exc),
        }
