"""User-authored plans and immutable saved revisions. No LLM calls."""
from datetime import datetime, timezone
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from .models import BusinessPlan, PlanRevision

SECTION_TITLES = {
    "customer": "Asiakas ja ongelma",
    "offering": "Tarjottava palvelu",
    "competition": "Kilpailijat ja erottautuminen",
    "sales": "Asiakashankinta",
    "finance": "Alustava talous",
    "assumptions": "Avoimet oletukset",
}


class CreatePlan(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=160)


class EditSection(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    content: str = Field(max_length=12000)
    action: Literal["save", "approve"] = "save"
    version: int = Field(ge=1)


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def owned_plan(db, owner_id, plan_id):
    plan = db.query(BusinessPlan).filter_by(id=plan_id, user_id=owner_id).first()
    if plan is None:
        raise HTTPException(404, "Suunnitelmaa ei löytynyt.")
    return plan


def serialize(plan):
    return {"id": plan.id, "title": plan.title, "sections": plan.sections,
            "version": plan.version, "updated_at": plan.updated_at}


def detail(db, plan):
    result = serialize(plan)
    result["revisions"] = [{"version": r.version, "created_at": r.created_at,
                            "description": r.description, "sections": r.sections}
                           for r in db.query(PlanRevision).filter_by(plan_id=plan.id)
                           .order_by(PlanRevision.version.desc()).limit(50)]
    return result


def create(db, owner_id, title):
    now = timestamp()
    sections = {key: {"title": title, "content": "", "status": "empty"} for key, title in SECTION_TITLES.items()}
    plan = BusinessPlan(user_id=owner_id, title=title, sections=sections, version=1, updated_at=now)
    db.add(plan)
    db.flush()
    db.add(PlanRevision(plan_id=plan.id, version=1, created_at=now,
                        description="Suunnitelma luotu", sections=sections))
    db.commit()
    return detail(db, plan)


def edit(db, owner_id, plan_id, key, data):
    plan = owned_plan(db, owner_id, plan_id)
    if key not in SECTION_TITLES:
        raise HTTPException(404, "Osiota ei löytynyt.")
    if data.version != plan.version:
        raise HTTPException(409, "Suunnitelma on muuttunut toisessa näkymässä. Avaa ajantasainen versio ennen tallentamista.")
    if data.action == "approve" and not data.content:
        raise HTTPException(422, "Kirjoita osion sisältö ennen hyväksymistä.")
    sections = {k: dict(v) for k, v in plan.sections.items()}
    changed = sections[key]["content"] != data.content
    status = "approved" if data.action == "approve" else ("draft" if data.content else "empty")
    if not changed and data.action == "save":
        return detail(db, plan)
    if not changed and sections[key]["status"] == status:
        return detail(db, plan)
    sections[key].update(content=data.content, status=status)
    # Later sections may rely on earlier choices; retain text but require review.
    if changed:
        keys = list(SECTION_TITLES)
        for dependent in keys[keys.index(key) + 1:]:
            if sections[dependent]["status"] == "approved":
                sections[dependent]["status"] = "review"
    now, version = timestamp(), plan.version + 1
    updated = db.query(BusinessPlan).filter_by(id=plan.id, user_id=owner_id, version=data.version).update(
        {"sections": sections, "version": version, "updated_at": now}, synchronize_session=False)
    if updated != 1:
        db.rollback()
        raise HTTPException(409, "Suunnitelma muuttui tallennuksen aikana. Avaa ajantasainen versio.")
    action = "hyväksytty" if data.action == "approve" else "tallennettu luonnoksena"
    db.add(PlanRevision(plan_id=plan.id, version=version, created_at=now,
                        description=f"{SECTION_TITLES[key]}: {action}", sections=sections))
    db.commit()
    db.refresh(plan)
    return detail(db, plan)
