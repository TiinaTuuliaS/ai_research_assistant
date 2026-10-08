"""Apply bounded, exact edits to an existing draft, never regenerate it."""
from pydantic import BaseModel, ConfigDict, Field


class ReportEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    original: str = Field(min_length=1, max_length=2000, description="Exact unique excerpt from the saved draft")
    replacement: str = Field(max_length=2500, description="Corrected excerpt; empty to remove an unsupported claim")


class ReportRepair(BaseModel):
    model_config = ConfigDict(extra="forbid")
    edits: list[ReportEdit] = Field(max_length=12)


def apply_repair(draft: str, repair: ReportRepair) -> str:
    spans = []
    for edit in repair.edits:
        if not edit.original.strip() or draft.count(edit.original) != 1:
            raise ValueError("Korjattavaa tekstikohtaa ei voitu tunnistaa yksiselitteisesti.")
        start = draft.index(edit.original)
        spans.append((start, start + len(edit.original), edit.replacement))
    spans.sort()
    if any(left[1] > right[0] for left, right in zip(spans, spans[1:])):
        raise ValueError("Korjausehdotukset kohdistuivat päällekkäisiin tekstikohtiin.")
    result = draft
    for start, end, replacement in reversed(spans):
        result = result[:start] + replacement + result[end:]
    if not result.strip():
        raise ValueError("Korjauksesta ei jäänyt luettavaa raporttia.")
    return result
