from sqlalchemy import Column, Integer, String, Text
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
    username = Column(String, unique=True)
    password = Column(String)