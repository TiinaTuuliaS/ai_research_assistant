from sqlalchemy import Column, Integer, String, Text, ForeignKey
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
