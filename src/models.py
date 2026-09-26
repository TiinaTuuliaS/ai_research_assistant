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


class ResearchJob(Base):
    __tablename__ = "research_jobs"

    id = Column(String(32), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    research_id = Column(Integer, ForeignKey("researches.id"), unique=True)
    topic = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued")
    steps = Column(JSON, nullable=False)
    error = Column(Text)


class BusinessPlan(Base):
    __tablename__ = "business_plans"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(160), nullable=False)
    sections = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(String, nullable=False)


class PlanRevision(Base):
    __tablename__ = "plan_revisions"
    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("business_plans.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    created_at = Column(String, nullable=False)
    description = Column(String, nullable=False)
    sections = Column(JSON, nullable=False)
