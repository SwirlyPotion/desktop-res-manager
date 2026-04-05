"""SQLAlchemy engine and session setup."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

from app.db.config import load_settings


class Base(DeclarativeBase):
    pass


settings = load_settings()
engine = create_engine(settings.database_url, future=True, pool_pre_ping=True)
SessionLocal = scoped_session(
    sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
)


def init_db() -> None:
    # Imported here to ensure model classes are registered before create_all.
    import app.db.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
