"""Database engine and session setup.

Purpose: Configure SQLAlchemy base, engine, and dependency session provider.
Callers: ORM models, API routes, database initialization.
Deps: SQLAlchemy, app.config.
API: Base, engine, SessionLocal, get_db.
Side effects: Creates SQLAlchemy engine at import time.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
connect_args = {'check_same_thread': False} if settings.database_url.startswith('sqlite') else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
