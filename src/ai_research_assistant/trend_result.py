"""Source-bound trends passed to the existing downstream tasks."""
from typing import Literal
import re

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .research_result import NonEmptyText, ResearchFinding


class TrendFinding(ResearchFinding):
    trend_kind: Literal["observed_change", "forecast", "example"] = Field(
        description="Observed change requires dated comparison; a forecast is not observed growth; a single case is an example")
    local_relevance: NonEmptyText = Field(max_length=700,
        description="Why this matters to the target market, including limits to transferring evidence from another area")


class TrendResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic: NonEmptyText = Field(max_length=500)
    findings: list[TrendFinding] = Field(max_length=3,
        description="Up to three source-backed trends or examples; empty if evidence is insufficient")


def render_trends(result, language="suomi", sources=None):
    fi = language != "english"
    urls = {str(HttpUrl(url)): url for url in (sources or {})}
    labels = {"observed_change": "Havaittu muutos", "forecast": "Ennuste", "example": "Yksittäinen esimerkki"}
    lines = ["## " + ("Muutoksen merkit" if fi else "Signals of change")]
    if not result.findings:
        lines.append("Lähteistä ei saatu vahvistettua kehityssuuntaa. Tämä ei osoita, ettei muutosta olisi."
                     if fi else "No trend could be substantiated from the sources. This does not establish absence of change.")
    for finding in result.findings:
        url = urls.get(str(finding.source), str(finding.source))
        lines.extend([f"### {finding.title}",
            f"**{labels[finding.trend_kind] if fi else finding.trend_kind}** · "
            + (finding.area or ("Alue ei selviä" if fi else "Area unknown")) + " · "
            + (finding.period or ("Ajankohta ei selviä" if fi else "Period unknown")),
            finding.summary, f"[{'Lähde' if fi else 'Source'}]({url})",
            ("Merkitys kohdemarkkinalle: " if fi else "Relevance to the target market: ") + finding.local_relevance,
            ("Rajaukset: " if fi else "Limitations: ") + " ".join(finding.limitations)])
        if finding.source_id:
            lines.append(("Lähdetunniste: " if fi else "Source ID: ") + f"[{finding.source_id}]")
    return "\n\n".join(lines)


def attach_trend_evidence(raw, sources, language="suomi"):
    """Keep the accepted trend provenance visible even if the writer omits it."""
    from .citations import SOURCE_HEADING
    findings = [finding for source in sources.values() for finding in source.get("trend_findings", [])]
    if not findings:
        return raw
    raw = re.sub(r"(?ms)^## (?:Trendien lähteet ja rajaukset|Trend sources and limitations)\s*\n.*?(?=^## |\Z)", "", raw)
    # finding_id is checkpoint metadata, not part of the model contract.
    result = TrendResult(topic="Trends", findings=[
        {key: value for key, value in finding.items() if key != "finding_id"} for finding in findings])
    section = render_trends(result, language, sources).replace(
        "## Muutoksen merkit", "## Trendien lähteet ja rajaukset", 1).replace(
        "## Signals of change", "## Trend sources and limitations", 1)
    heading = SOURCE_HEADING.search(raw)
    if heading:
        return raw[:heading.start()].rstrip() + "\n\n" + section + "\n\n" + raw[heading.start():]
    return raw.rstrip() + "\n\n" + section
