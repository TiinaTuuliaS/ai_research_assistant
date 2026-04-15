from sqlalchemy import Column, Integer, String, Text
from .database import Base

class Research(Base):
    __tablename__ = "researches"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String)
    result = Column(Text) 