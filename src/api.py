from fastapi import FastAPI
from datetime import datetime
import os
import re
from .database import SessionLocal, engine
from .models import Research, Base

from src.ai_research_assistant.crew import AiResearchAssistant
from src.ai_research_assistant.pdf_utils import create_pdf

Base.metadata.create_all(bind=engine)

app = FastAPI()

# 🔥 CORS (tärkeä Reactille)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "API toimii"}


@app.post("/research")
def research(data: dict):
    topic = data.get("topic")
    language = data.get("language", "suomi")

    inputs = {
        "topic": topic,
        "current_year": "2026",
        "language": language
    }

    result = AiResearchAssistant().crew().kickoff(inputs=inputs)

    # 🔥 TALLENNUS
    db = SessionLocal()

    new_research = Research(
        topic=topic,
        result=str(result)
    )

    db.add(new_research)
    db.commit()
    db.close()

    return {"result": str(result)}

@app.get("/researches")
def get_researches():
    db = SessionLocal()
    researches = db.query(Research).all()
    db.close()

    return [
        {
            "id": r.id,
            "topic": r.topic,
            "result": r.result
        }
        for r in researches
    ]