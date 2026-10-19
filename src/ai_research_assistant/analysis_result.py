"""The analyst's decision, tied to the accepted observation ledger."""
from typing import Literal
import re

from pydantic import BaseModel, ConfigDict, Field

from .research_result import NonEmptyText


class Conclusion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    statement: NonEmptyText
    finding_ids: list[str] = Field(max_length=12)
    uncertainty: NonEmptyText


class Comparison(BaseModel):
    model_config = ConfigDict(extra="forbid")
    competitor: str = Field(default='', description='Display name resolved from competitor_id by the server.')
    competitor_id: str = Field(default='', description='Exact entity_id (E1 etc.) from accepted findings. Never invent an ID.')
    feature: NonEmptyText
    status: Literal["shared", "evidenced_difference", "proposal", "unknown"]
    finding_ids: list[str] = Field(min_length=1, max_length=12)
    limitation: NonEmptyText


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    research_type: Literal["demand", "competition", "market"]
    topic: NonEmptyText
    answer: Conclusion
    conclusions: list[Conclusion] = Field(max_length=6)
    comparisons: list[Comparison] = Field(max_length=6)
    recommendation: NonEmptyText
    alternative: NonEmptyText
    gaps: list[NonEmptyText] = Field(min_length=1, max_length=6)

    def validate_evidence(self, findings, brief):
        if self.research_type != brief.get("research_type") or self.topic != brief.get("topic"):
            raise ValueError("Preserve the requested research_type and topic exactly.")
        ledger = {item["finding_id"]: item for item in findings}
        for conclusion in [self.answer, *self.conclusions, *self.comparisons]:
            if set(conclusion.finding_ids) - ledger.keys():
                raise ValueError("Use only accepted finding IDs from the research context.")
        for conclusion in [self.answer, *self.conclusions]:
            # The requested time range is not evidence. Check each conclusion
            # against its own observations, never another conclusion's sources.
            support = " ".join(
                str(ledger[key].get(field) or "")
                for key in conclusion.finding_ids
                for field in ("supporting_text", "period_support")
            )
            years = lambda text: set(re.findall(r"\b(?:19|20)\d{2}\b", text))
            if years(conclusion.statement) - years(support):
                raise ValueError("The conclusion adds a year absent from its referenced evidence. "
                                 "Narrow the statement to the supported dates; put the requested "
                                 "but unverified time range in gaps, not in a factual conclusion.")
        if ledger and not self.answer.finding_ids:
            raise ValueError("Tie the answer to at least one accepted finding.")
        if self.research_type != "competition" and self.comparisons:
            raise ValueError("comparisons is only for competition research.")
        for comparison in self.comparisons:
            entities = {ledger[key].get("entity") for key in comparison.finding_ids}
            if comparison.competitor not in entities:
                raise ValueError("The competitor must match an entity in the referenced findings.")
            if comparison.status in {"shared", "evidenced_difference"} and len(entities - {None, ""}) < 2:
                raise ValueError("A shared feature or evidenced difference requires observations about both compared entities. Use unknown when the other side is unverified.")


def render_analysis(result, findings, language="suomi"):
    fi = language.lower() in {"suomi", "fi", "finnish"}
    ledger = {item["finding_id"]: item for item in findings}
    def citations(ids):
        # Preserve registry IDs even when filtering leaves gaps in numbering.
        urls = {str(ledger[key]["source"]): ledger[key].get("source_id", "") for key in ids}
        label = "Lähde" if fi else "Source"
        return " ".join(f"[{label}{' ' + sid if sid else ''}]({url})" for url, sid in urls.items())
    lines = ["## " + ("Vastaus kysymykseesi" if fi else "Answer")]
    for conclusion in [result.answer, *result.conclusions]:
        lines.extend([conclusion.statement + " " + citations(conclusion.finding_ids),
                      conclusion.uncertainty])
    labels = {"shared": "Yhteinen ominaisuus", "evidenced_difference": "Osoitettu ero",
              "proposal": "Testattava ehdotus", "unknown": "Ei vahvistettu"}
    for comparison in result.comparisons:
        lines.extend([f"### {comparison.competitor}: {comparison.feature}",
                      labels[comparison.status] if fi else comparison.status,
                      comparison.limitation + " " + citations(comparison.finding_ids)])
    lines.extend(["## " + ("Suositus" if fi else "Recommendation"), result.recommendation,
                  "## " + ("Vaihtoehto" if fi else "Alternative"), result.alternative,
                  "## " + ("Tiedon puutteet" if fi else "Evidence gaps"),
                  "\n".join(f"- {gap}" for gap in result.gaps)])
    return "\n\n".join(lines)
