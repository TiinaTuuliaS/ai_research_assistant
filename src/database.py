import os
from pathlib import Path

from sqlalchemy import create_engine, event
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


def get_db():
    with SessionLocal() as db:
        yield db

