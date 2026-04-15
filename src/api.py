from fastapi import FastAPI
from datetime import datetime
import os
import re

from src.ai_research_assistant.crew import AiResearchAssistant
from src.ai_research_assistant.pdf_utils import create_pdf

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
def run_research(data: dict):
    topic = data.get("topic", "").strip()
    language = data.get("language", "suomi")

    if not topic:
        return {"error": "Anna tutkimusaihe"}

    inputs = {
        "topic": topic,
        "current_year": str(datetime.now().year),
        "language": language
    }

    result = AiResearchAssistant().crew().kickoff(inputs=inputs)

    os.makedirs("reports", exist_ok=True)

    safe_topic = re.sub(r'[^a-zA-Z0-9_]', '', topic.replace(" ", "_")).lower()

    # TXT
    txt_path = f"reports/{safe_topic}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(str(result))

    # PDF
    pdf_filename = f"{safe_topic}.pdf"
    pdf_path = create_pdf(str(result), pdf_filename)

    return {
        "result": str(result),
        "txt_path": txt_path,
        "pdf_path": pdf_path
    }