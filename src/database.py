import os
from pathlib import Path

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL", f"sqlite:///{Path(__file__).resolve().parents[1] / 'app.db'}"
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite:") else {}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


if DATABASE_URL.startswith("sqlite:"):
    @event.listens_for(engine, "connect")
    def configure_sqlite(connection, _):
        connection.execute("PRAGMA secure_delete=ON")
        connection.execute("PRAGMA foreign_keys=ON")


def migrate_research_dates(bind):
    """Add nullable UTC timestamps without inventing dates for legacy rows."""
    with bind.begin() as connection:
        for table in ("researches", "research_jobs"):
            columns = {column["name"] for column in inspect(connection).get_columns(table)}
            if "created_at" not in columns:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN created_at VARCHAR"))


def get_db():
    with SessionLocal() as db:
        yield db

