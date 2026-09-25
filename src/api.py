from contextlib import asynccontextmanager
from datetime import datetime
import os
import secrets
import time
from typing import Literal

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, text
from sqlalchemy.orm import Session

load_dotenv()

from .database import SessionLocal, engine, get_db
from .models import Base, LoginSession, Research, User
from .security import hash_password, is_password_hash, token_hash, verify_password

COOKIE_NAME = "research_session"
SESSION_SECONDS = 12 * 60 * 60
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv(
    "ALLOWED_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000"
).split(",") if origin.strip()]
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


def migrate_passwords(db: Session):
    """Upgrade accounts in place, retaining user IDs and research ownership."""
    for user in db.query(User).all():
        if not is_password_hash(user.password):
            user.password = hash_password(user.password or secrets.token_urlsafe(32))
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        migrate_passwords(db)
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_credentials=True,
    allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-Requested-With"],
)


@app.middleware("http")
async def protect_requests(request: Request, call_next):
    # This header forces browser cross-origin writes through CORS preflight.
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if (origin and origin not in ALLOWED_ORIGINS) or request.headers.get(
            "x-requested-with"
        ) != "ResearchApp":
            return JSONResponse(status_code=403, content={"detail": "Pyyntö ei ole sallittu."})
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=1024)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise ValueError("Anna sähköposti tai käyttäjätunnus.")
        return value


class SignupCredentials(Credentials):
    password: str = Field(min_length=12, max_length=1024)


class ResearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    topic: str = Field(min_length=1, max_length=500)
    language: Literal["suomi", "english"] = "suomi"


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME, "")
    session = db.get(LoginSession, token_hash(token)) if token else None
    if not session or session.expires_at <= int(time.time()):
        raise HTTPException(401, "Istunto on vanhentunut. Kirjaudu sisään.")
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(401, "Kirjaudu sisään.")
    return user


@app.get("/")
def root():
    return {"message": "API toimii"}


@app.post("/signup", status_code=201)
def signup(data: SignupCredentials, db: Session = Depends(get_db)):
    password = hash_password(data.password)
    # Serialize checks on the existing SQLite table, which lacks a unique constraint.
    if db.bind.dialect.name == "sqlite":
        db.execute(text("BEGIN IMMEDIATE"))
    if db.query(User).filter(func.lower(func.trim(User.email)) == data.email).first():
        raise HTTPException(409, "Tunnus on jo käytössä.")
    db.add(User(email=data.email, password=password))
    db.commit()
    return {"message": "Tili luotu. Voit kirjautua sisään."}


@app.post("/login")
def login(data: Credentials, request: Request, response: Response, db: Session = Depends(get_db)):
    candidates = db.query(User).filter(func.lower(func.trim(User.email)) == data.email).all()
    user = next((u for u in candidates if verify_password(data.password, u.password)), None)
    if not candidates:
        verify_password(data.password, DUMMY_PASSWORD_HASH)
    if not user:
        raise HTTPException(401, "Virheellinen tunnus tai salasana.")
    old_token = request.cookies.get(COOKIE_NAME)
    if old_token:
        db.query(LoginSession).filter_by(token_hash=token_hash(old_token)).delete()
    db.query(LoginSession).filter(LoginSession.expires_at <= int(time.time())).delete()
    token = secrets.token_urlsafe(32)
    db.add(LoginSession(token_hash=token_hash(token), user_id=user.id,
                        expires_at=int(time.time()) + SESSION_SECONDS))
    db.commit()
    response.set_cookie(COOKIE_NAME, token, max_age=SESSION_SECONDS,
                        httponly=True, secure=COOKIE_SECURE, samesite="strict", path="/")
    return {"user_id": user.id, "email": user.email}


@app.get("/me")
def me(user: User = Depends(current_user)):
    return {"user_id": user.id, "email": user.email}


@app.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE_NAME, "")
    db.query(LoginSession).filter_by(token_hash=token_hash(token)).delete()
    db.commit()
    response.delete_cookie(COOKIE_NAME, path="/", httponly=True,
                           secure=COOKIE_SECURE, samesite="strict")


def generate_report(topic: str, language: str) -> str:
    from .ai_research_assistant.crew import AiResearchAssistant
    return AiResearchAssistant().crew().kickoff(inputs={
        "topic": topic, "language": language, "current_year": str(datetime.now().year)
    }).raw


@app.post("/research")
def research(data: ResearchRequest, request: Request,
             user: User = Depends(current_user), db: Session = Depends(get_db)):
    owner_id = user.id
    # End the read transaction before the potentially long external call.
    db.commit()
    try:
        result = generate_report(data.topic, data.language)
    except Exception:
        raise HTTPException(502, "Tutkimus tai lähteiden tarkistus epäonnistui. Yritä uudelleen.") from None
    db.expire_all()
    current_user(request, db)
    entry = Research(topic=data.topic, result=result, user_id=owner_id)
    db.add(entry)
    db.commit()
    return {"id": entry.id, "topic": entry.topic, "result": entry.result}


@app.get("/researches")
def get_researches(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [{"id": r.id, "topic": r.topic, "result": r.result}
            for r in db.query(Research).filter_by(user_id=user.id).order_by(Research.id.desc()).all()]


@app.get("/researches/{user_id}", include_in_schema=False)
def legacy_researches(user_id: int, user: User = Depends(current_user),
                      db: Session = Depends(get_db)):
    if user_id != user.id:
        raise HTTPException(403, "Ei käyttöoikeutta.")
    return get_researches(user, db)
