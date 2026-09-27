from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from .database import Base

class Research(Base):
    __tablename__ = "researches"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String)
    result = Column(Text)
    user_id = Column(Integer)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String)
    password = Column(String)


class LoginSession(Base):
    __tablename__ = "login_sessions"

    token_hash = Column(String(64), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(Integer, nullable=False, index=True)


class ResearchUsage(Base):
    __tablename__ = "research_usage"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    used = Column(Integer, nullable=False, default=0)


class ResearchJob(Base):
    __tablename__ = "research_jobs"

    id = Column(String(32), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    research_id = Column(Integer, ForeignKey("researches.id"), unique=True)
    topic = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued")
    steps = Column(JSON, nullable=False)
    error = Column(Text)
