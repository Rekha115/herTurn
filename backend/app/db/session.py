import os
import logging
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from .base import Base
# Import models so Base.metadata knows about all registered tables
from . import models  # noqa: F401

logger = logging.getLogger("herturn.db")

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = BACKEND_DIR / "herturn.db"


def get_database_url() -> str:
    """
    Resolves the active database connection URL.
    Priority:
      1. DATABASE_URL environment variable
      2. HERTURN_DB_PATH environment variable (converted to SQLite URI)
      3. Default local SQLite file at backend/herturn.db
    """
    env_url = os.getenv("DATABASE_URL")
    if env_url and env_url.strip():
        # Handle Render/Heroku postgres:// -> postgresql:// dialect prefix if needed
        if env_url.startswith("postgres://"):
            return env_url.replace("postgres://", "postgresql://", 1)
        return env_url.strip()

    custom_path = os.getenv("HERTURN_DB_PATH")
    if custom_path and custom_path.strip():
        db_file = Path(custom_path.strip()).resolve()
        db_file.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_file}"

    # Default local SQLite database
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{DEFAULT_DB_PATH}"


DATABASE_URL = get_database_url()
is_sqlite = DATABASE_URL.startswith("sqlite")

engine_kwargs = {}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)


# Enable SQLite foreign key constraints (disabled by default in SQLite)
if is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        except Exception as e:
            logger.warning(f"Could not enable SQLite foreign_keys PRAGMA: {e}")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(target_engine: Engine = None) -> None:
    """
    Idempotent database table initialization.
    Safely creates all registered tables if they do not already exist.
    """
    active_engine = target_engine or engine
    logger.info(f"Initializing HerTurn database tables on: {active_engine.url}")
    Base.metadata.create_all(bind=active_engine)

    # Idempotently migrate missing columns on existing SQLite/PostgreSQL schemas
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(active_engine)
        table_names = inspector.get_table_names()
        if "roadmap_records" in table_names:
            existing_cols = [c["name"] for c in inspector.get_columns("roadmap_records")]
            if "resume_analysis_id" not in existing_cols:
                logger.info("Migrating roadmap_records table: adding resume_analysis_id column")
                with active_engine.connect() as conn:
                    conn.execute(text("ALTER TABLE roadmap_records ADD COLUMN resume_analysis_id INTEGER REFERENCES resume_analysis_records(id) ON DELETE SET NULL"))
                    conn.commit()
    except Exception as mig_err:
        logger.warning(f"Note on roadmap_records schema migration check: {mig_err}")


def reset_db(target_engine: Engine = None) -> None:
    """
    Drops all registered tables and recreates them.
    Useful for test suites and fresh sandbox resets.
    """
    active_engine = target_engine or engine
    logger.warning(f"Resetting HerTurn database tables on: {active_engine.url}")
    Base.metadata.drop_all(bind=active_engine)
    Base.metadata.create_all(bind=active_engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a scoped database session
    and guarantees closure upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
