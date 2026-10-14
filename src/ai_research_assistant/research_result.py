"""The research stage's validated output contract."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints, WithJsonSchema, field_serializer, field_validator
from pydantic.json_schema import SkipJsonSchema


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
# CrewAI 1.10 strips null from output schemas. Represent unknown scope as an
# empty string on the wire and normalize it to None in validated findings.
OptionalEvidenceText = Annotated[
    NonEmptyText | None, WithJsonSchema({"type": "string"})
]


class ResearchOutputError(ValueError):
    """The research stage cannot safely pass its output to downstream tasks."""


class ResearchFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: NonEmptyText = Field(max_length=200)
    summary: NonEmptyText = Field(max_length=2000)
    source: str = Field(description="Registered source ID, e.g. S1, from citation_sources. Never write a URL.")
    source_id: SkipJsonSchema[str] = Field(default="")
    supporting_text: str = Field(default="", max_length=1600,
        description="One short exact passage from this source supporting this single observation. Private evidence, never report prose.")
    period_support: str = Field(default="", max_length=500,
        description="Exact source passage supporting the observation period. Empty if period is unknown; publication and retrieval dates are not observation periods.")
    relevance: int = Field(strict=True, ge=1, le=10,
                           description="Relevance to the user's topic, not confidence or proof of demand")
    # Server-owned evidence, deliberately absent from the model's output schema
    # and from serialization/UI. Old stored findings can still be loaded.
    evidence_excerpt: SkipJsonSchema[str] = Field(default="", exclude=True)
    evidence_kind: Literal["offering", "price", "usage", "purchase", "interest", "marketing_claim", "other"]
    entity: OptionalEvidenceText = Field(description="Company, branch or population explicitly identified by the source; empty string if unknown")
    area: OptionalEvidenceText = Field(description="Geographical scope explicitly supported by the source; empty string if unknown")
    period: OptionalEvidenceText = Field(description="Time the observation concerns, not retrieval date; empty string if unknown")
    limitations: list[NonEmptyText] = Field(min_length=1, max_length=5,
        description="What this observation cannot establish; never treat missing information as absence")

    @field_validator("source", mode="before")
    @classmethod
    def validate_source(cls, value):
        from .source_registry import SOURCE_ID
        if isinstance(value, str) and SOURCE_ID.fullmatch(value):
            return value
        return str(HttpUrl(value))  # Compatibility for saved URL-based findings.

    @field_validator("entity", "area", "period", mode="before")
    @classmethod
    def normalize_unknown_scope(cls, value):
        return None if isinstance(value, str) and not value.strip() else value

    @field_serializer("source")
    def serialize_source(self, source: str) -> str:
        # CrewAI 1.10 also JSON-encodes model_dump() in its execution log.
        return str(source)


class ResearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: NonEmptyText = Field(max_length=500)
    findings: list[ResearchFinding] = Field(max_length=12,
        description="Source-backed findings. Return an empty list if none were found; never invent findings.")


def render_research(result: ResearchResult, language: str = "suomi", sources: dict | None = None,
                    excluded: list[str] | None = None) -> str:
    """Keep existing Markdown consumers while retaining TaskOutput.pydantic."""
    fi = language != "english"
    # Pydantic normalizes URLs; display the exact registered URL when available.
    urls = {str(HttpUrl(url)): url for url in (sources or {})}
    lines = [f"## {result.topic}"]
    if not result.findings:
        lines.append("Tutkimuksessa ei löytynyt aiheeseen sopivia lähteistettyjä havaintoja."
                     if fi else "No relevant source-backed findings were found.")
    kinds = {"offering": "Tarjonta", "price": "Pyyntihinta", "usage": "Toteutunut käyttö",
             "purchase": "Toteutunut osto", "interest": "Kiinnostus", "marketing_claim": "Markkinointiväite", "other": "Muu havainto"}
    for index, finding in enumerate(result.findings, 1):
        url = urls.get(str(finding.source), str(finding.source))
        lines.extend([f"### {finding.title}", finding.summary,
                      (f"[Lähde]({url}) · Osuvuus aiheeseen: {finding.relevance}/10"
                       if fi else f"[Source]({url}) · Relevance to topic: {finding.relevance}/10")])
        if finding.source_id:
            lines.append(("Lähdetunniste: " if fi else "Source ID: ") + f"[{finding.source_id}]")
        scope = " · ".join(value for value in (finding.entity, finding.area, finding.period) if value)
        lines.extend([
            f"**{kinds[finding.evidence_kind] if fi else finding.evidence_kind}** — " + (scope or ("Kohde, alue ja ajankohta eivät selviä." if fi else "Scope and date unknown.")),
            ("Rajaukset: " if fi else "Limitations: ") + " ".join(finding.limitations),
        ])
    if result.findings:
        lines.append("Osuvuus kuvaa yhteyttä aiheeseen, ei lähteen luotettavuutta tai kysynnän vahvuutta."
                     if fi else "Relevance measures fit to the topic, not source reliability or strength of demand.")
    lines.append("Kartoitus ei ole kattava. Löydetyt toimijat ovat esimerkkejä, eivät alueen kokonaismäärä. "
                 "Hakutuloksista puuttuminen ei osoita, ettei toimijaa tai palvelua ole olemassa."
                 if fi else "This search is not exhaustive. Found providers are examples, not the area's total. "
                 "Absence from search results does not establish that a provider or service does not exist.")
    return "\n\n".join(lines)
