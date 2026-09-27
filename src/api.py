from contextlib import asynccontextmanager
from datetime import datetime
import os
import secrets
import time
import sys
import logging
import traceback
from threading import RLock
from typing import Literal

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, text
from sqlalchemy.orm import Session

load_dotenv()

# Windows redirected consoles otherwise fail on CrewAI's Unicode status output.
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
logger = logging.getLogger(__name__)

from .database import SessionLocal, engine, get_db
from .models import Base, LoginSession, Research, ResearchJob, ResearchUsage, User
from .security import hash_password, is_password_hash, token_hash, verify_password

COOKIE_NAME = "research_session"
SESSION_SECONDS = 12 * 60 * 60
RESEARCH_LIMIT = 3
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv(
    "ALLOWED_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000"
).split(",") if origin.strip()]
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))
job_lock = RLock()
STEPS = [
    ("researcher", "Tutkija", "Kartoittaa markkinat ja kilpailijat"),
    ("trend_analyst", "Trendianalyytikko", "Etsii muutoksia ja uusia signaaleja"),
    ("analyst", "Markkina-analyytikko", "Arvioi kysyntää ja epävarmuuksia"),
    ("strategist", "Strategi", "Punnitsee vaihtoehtoja ja suosituksia"),
    ("writer", "Raportin kirjoittaja", "Yhdistää näkemykset ja tarkistaa lähdeviitteet"),
]


def new_steps():
    return [dict(key=key, label=label, description=description, status="pending", output="")
            for key, label, description in STEPS]


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
        for job in db.query(ResearchJob).filter(ResearchJob.status.in_(["queued", "running"])):
            job.status = "failed"
            job.error = "Palvelin käynnistyi uudelleen ja tutkimus keskeytyi."
            job.steps = [{**step, "status": "failed" if step["status"] == "running" else step["status"]}
                         for step in job.steps]
        db.commit()
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
    goal: str = Field(default="", max_length=1000)
    target_market: str = Field(default="", max_length=500)
    budget_eur: float | None = Field(default=None, ge=0, le=10_000_000, allow_inf_nan=False)
    research_type: Literal["demand", "competition", "market"] | None = None
    problem: str = Field(default="", max_length=1000)
    competitors: str = Field(default="", max_length=1000)


def research_goal(data: ResearchRequest) -> str:
    """User decision context only; per-agent responsibilities live in deliverables.yaml."""
    if data.research_type == "demand":
        return "Assess demand for this idea among the specified customers. Customer problem: " + data.problem
    if data.research_type == "competition":
        return ("Compare competitors against the user's solution and evaluate differentiation. "
                "User-provided competitors (unverified; discover alternatives if empty): " + data.competitors)
    if data.research_type == "market":
        return "Map this industry and region to answer the user's question: " + data.goal
    return data.goal


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME, "")
    session = db.get(LoginSession, token_hash(token)) if token else None
    if not session or session.expires_at <= int(time.time()):
        raise HTTPException(401, "Istunto on vanhentunut. Kirjaudu sisään.")
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(401, "Kirjaudu sisään.")
    return user


def research_quota(db: Session, user_id: int):
    with job_lock:
        usage = db.get(ResearchUsage, user_id)
        if usage is None:
            # Import existing attempts once, without counting a job's report twice.
            jobs = db.query(ResearchJob).filter_by(user_id=user_id).count()
            legacy = db.query(Research).filter(
                Research.user_id == user_id,
                ~db.query(ResearchJob).filter(ResearchJob.research_id == Research.id).exists(),
            ).count()
            usage = ResearchUsage(user_id=user_id, used=jobs + legacy)
            db.add(usage)
            db.commit()
        db.refresh(usage)
        return {"limit": RESEARCH_LIMIT, "used": usage.used,
                "remaining": max(0, RESEARCH_LIMIT - usage.used)}


def reserve_research(db: Session, user_id: int):
    """Reserve before any paid call; the caller commits with the new job, if any."""
    research_quota(db, user_id)
    changed = db.query(ResearchUsage).filter(
        ResearchUsage.user_id == user_id, ResearchUsage.used < RESEARCH_LIMIT,
    ).update({ResearchUsage.used: ResearchUsage.used + 1}, synchronize_session=False)
    if not changed:
        db.rollback()
        raise HTTPException(429, detail={
            "message": "Olet käyttänyt tilisi kaikki kolme tutkimusta. Voit edelleen katsella ja tallentaa omia raporttejasi.",
            "quota": research_quota(db, user_id),
        })


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
    return {"user_id": user.id, "email": user.email, "quota": research_quota(db, user.id)}


@app.get("/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return {"user_id": user.id, "email": user.email, "quota": research_quota(db, user.id)}


@app.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE_NAME, "")
    db.query(LoginSession).filter_by(token_hash=token_hash(token)).delete()
    db.commit()
    response.delete_cookie(COOKIE_NAME, path="/", httponly=True,
                           secure=COOKIE_SECURE, samesite="strict")


def generate_report(topic: str, language: str, goal: str = "",
                    target_market: str = "", budget_eur: float | None = None, progress=None, research_type=None):
    from .ai_research_assistant.crew import AiResearchAssistant
    from .ai_research_assistant.progress import track_tasks
    crew = AiResearchAssistant().crew()
    inputs = {
        "topic": topic, "language": language, "current_year": str(datetime.now().year),
        "goal": goal, "target_market": target_market,
        "research_type": research_type or "market",
        "budget": "Not specified; do not assume a budget" if budget_eur is None else f"{budget_eur:g} EUR",
    }
    if progress is None:
        return crew.kickoff(inputs=inputs).raw
    with track_tasks(crew, progress):
        return crew.kickoff(inputs=inputs).raw


def job_payload(job, db):
    entry = db.get(Research, job.research_id) if job.research_id else None
    return {"id": job.id, "topic": job.topic, "status": job.status,
            "steps": job.steps, "error": job.error,
            "result": entry.result if entry else "", "research_id": job.research_id,
            "quota": research_quota(db, job.user_id)}


def update_progress(job_id, index, status, output):
    with job_lock, SessionLocal() as db:
        job = db.get(ResearchJob, job_id)
        if not job or job.status not in {"queued", "running"}:
            return
        steps = [dict(step) for step in job.steps]
        # A delayed start event must never roll back a completed task.
        if steps[index]["status"] == "completed":
            return
        steps[index].update(status=status, output=output or "")
        job.steps = steps
        job.status = "running"
        db.commit()


def run_job(job_id, data, session_hash):
    try:
        with SessionLocal() as db:
            session = db.get(LoginSession, session_hash)
            if not session or session.expires_at <= int(time.time()):
                raise PermissionError("Session expired")
        result = generate_report(data.topic, data.language, research_goal(data), data.target_market,
                                 data.budget_eur,
                                 **({"research_type": data.research_type} if data.research_type else {}),
                                 progress=lambda i, state, output: update_progress(job_id, i, state, output))
        with job_lock, SessionLocal() as db:
            job = db.get(ResearchJob, job_id)
            session = db.get(LoginSession, session_hash)
            if not session or session.user_id != job.user_id or session.expires_at <= int(time.time()):
                raise PermissionError("Session expired")
            entry = Research(topic=job.topic, result=result, user_id=job.user_id)
            db.add(entry)
            db.flush()
            job.research_id = entry.id
            job.status = "completed"
            db.commit()
    except Exception as exc:
        # Record locations and exception type, never prompts, keys or provider bodies.
        frames = " > ".join(f"{frame.name}:{frame.lineno}" for frame in traceback.extract_tb(exc.__traceback__))
        logger.error("Research job %s failed: %s at %s", job_id, type(exc).__name__, frames)
        with job_lock, SessionLocal() as db:
            job = db.get(ResearchJob, job_id)
            job.status = "failed"
            if isinstance(exc, PermissionError):
                job.error = "Istunto päättyi tutkimuksen aikana. Kirjaudu uudelleen sisään."
            elif isinstance(exc, UnicodeError):
                job.error = "Palvelimen tekstinkäsittelyssä tapahtui merkistövirhe."
            elif "guardrail" in str(exc).lower():
                job.error = "Loppuraportti ei läpäissyt lähteiden tai raportin rakenteen tarkistusta. Agenttien välitulokset ovat säilyneet."
            else:
                active = next((step["label"] for step in job.steps if step["status"] == "running"), "Tutkimuksen alustus")
                job.error = f"{active}: tutkimus keskeytyi palvelinvirheeseen. Virheen tekniset tiedot on kirjattu palvelimen lokiin."
            job.steps = [{**step, "status": "failed" if step["status"] == "running" else step["status"]}
                         for step in job.steps]
            db.commit()


@app.post("/research-jobs", status_code=202)
def start_job(data: ResearchRequest, request: Request, background: BackgroundTasks,
              user: User = Depends(current_user), db: Session = Depends(get_db)):
    with job_lock:
        active = db.query(ResearchJob).filter(ResearchJob.status.in_(["queued", "running"]))
        existing = active.filter_by(user_id=user.id).first()
        if existing:
            return job_payload(existing, db)
        if active.count() >= 2:
            raise HTTPException(429, "Palvelu tekee jo kahta tutkimusta. Kokeile hetken kuluttua.")
        reserve_research(db, user.id)
        job = ResearchJob(id=secrets.token_hex(16), user_id=user.id, topic=data.topic,
                          status="queued", steps=new_steps())
        db.add(job)
        db.commit()
        payload = job_payload(job, db)
        background.add_task(run_job, job.id, data, token_hash(request.cookies[COOKIE_NAME]))
        return payload


@app.get("/research-jobs/{job_id}")
def get_job(job_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    job = db.query(ResearchJob).filter_by(id=job_id, user_id=user.id).first()
    if not job:
        raise HTTPException(404, "Tutkimusta ei löytynyt.")
    return job_payload(job, db)


@app.post("/research")
def research(data: ResearchRequest, request: Request,
             user: User = Depends(current_user), db: Session = Depends(get_db)):
    owner_id = user.id
    with job_lock:
        reserve_research(db, owner_id)
        # Persist the charge before the external call, including failed attempts.
        db.commit()
    try:
        result = generate_report(data.topic, data.language, research_goal(data), data.target_market, data.budget_eur,
                                 **({"research_type": data.research_type} if data.research_type else {}))
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
    rows = db.query(Research, ResearchJob).outerjoin(
        ResearchJob, ResearchJob.research_id == Research.id
    ).filter(Research.user_id == user.id).order_by(Research.id.desc()).all()
    return [{"id": r.id, "topic": r.topic, "result": r.result,
             "steps": job.steps if job else []} for r, job in rows]


@app.get("/researches/{user_id}", include_in_schema=False)
def legacy_researches(user_id: int, user: User = Depends(current_user),
                      db: Session = Depends(get_db)):
    if user_id != user.id:
        raise HTTPException(403, "Ei käyttöoikeutta.")
    return get_researches(user, db)
