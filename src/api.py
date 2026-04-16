from fastapi import FastAPI
from datetime import datetime
import os
import re

from .database import SessionLocal, engine
from .models import Research, Base, User

from src.ai_research_assistant.crew import AiResearchAssistant
from src.ai_research_assistant.pdf_utils import create_pdf

# 🔥 Luo taulut
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 🔥 CORS (Reactia varten)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# ROOT
# ======================
@app.get("/")
def root():
    return {"message": "API toimii"}

# ======================
# SIGNUP
# ======================
# ======================
# SIGNUP
# ======================
@app.post("/signup")
def signup(data: dict):
    db = SessionLocal()

    user = User(
        email=data.get("email"),
        password=data.get("password")
    )

    db.add(user)
    db.commit()
    db.close()

    return {"message": "User created"}

# ======================
# LOGIN
# ======================
@app.post("/login")
def login(data: dict):
    email = data.get("email")
    password = data.get("password")

    db = SessionLocal()

    user = db.query(User).filter(User.email == email).first()

    if not user:
        return {"error": "user not found"}

    if user.password != password:
        return {"error": "wrong password"}

    return {"user_id": user.id}

# ======================
# RESEARCH
# ======================
@app.post("/research")
def research(data: dict):
    topic = data.get("topic")
    language = data.get("language", "suomi")
    user_id = data.get("user_id")

    inputs = {
        "topic": topic,
        "current_year": "2026",
        "language": language
    }

    result = AiResearchAssistant().crew().kickoff(inputs=inputs)

    db = SessionLocal()

    new_research = Research(
        topic=topic,
        result=str(result),
        user_id=user_id
    )

    db.add(new_research)
    db.commit()
    db.close()

    return {"result": str(result)}

# ======================
# GET USER RESEARCHES
# ======================
@app.get("/researches/{user_id}")
def get_researches(user_id: int):
    db = SessionLocal()

    researches = db.query(Research).filter(
        Research.user_id == user_id
    ).all()

    db.close()

    return [
        {
            "id": r.id,
            "topic": r.topic,
            "result": r.result
        }
        for r in researches
    ]