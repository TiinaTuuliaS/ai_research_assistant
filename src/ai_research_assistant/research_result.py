"""The research stage's validated output contract."""
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints, WithJsonSchema, field_serializer


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ResearchOutputError(ValueError):
    """The research stage cannot safely pass its output to downstream tasks."""


class ResearchFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: NonEmptyText = Field(max_length=200)
    summary: NonEmptyText = Field(max_length=2000)
    # Keep runtime URL validation; OpenAI does not support JSON Schema format=uri.
    source: Annotated[HttpUrl, WithJsonSchema({"type": "string", "description": "An HTTP or HTTPS source URL"})]
    relevance: int = Field(strict=True, ge=1, le=10,
                           description="Relevance to the user's topic, not confidence or proof of demand")

    @field_serializer("source")
    def serialize_source(self, source: HttpUrl) -> str:
        # CrewAI 1.10 also JSON-encodes model_dump() in its execution log.
        return str(source)


class ResearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: NonEmptyText = Field(max_length=500)
    findings: list[ResearchFinding] = Field(max_length=12,
        description="Source-backed findings. Return an empty list if none were found; never invent findings.")


def render_research(result: ResearchResult, language: str = "suomi", sources: dict | None = None) -> str:
    """Keep existing Markdown consumers while retaining TaskOutput.pydantic."""
    fi = language != "english"
    # Pydantic normalizes URLs; display the exact registered URL when available.
    urls = {str(HttpUrl(url)): url for url in (sources or {})}
    lines = [f"## {result.topic}"]
    if not result.findings:
        lines.append("Tutkimuksessa ei löytynyt aiheeseen sopivia lähteistettyjä havaintoja."
                     if fi else "No relevant source-backed findings were found.")
    for finding in result.findings:
        url = urls.get(str(finding.source), str(finding.source))
        lines.extend([f"### {finding.title}", finding.summary,
                      (f"[Lähde]({url}) · Osuvuus aiheeseen: {finding.relevance}/10"
                       if fi else f"[Source]({url}) · Relevance to topic: {finding.relevance}/10")])
    if result.findings:
        lines.append("Osuvuus kuvaa yhteyttä aiheeseen, ei lähteen luotettavuutta tai kysynnän vahvuutta."
                     if fi else "Relevance measures fit to the topic, not source reliability or strength of demand.")
    return "\n\n".join(lines)
