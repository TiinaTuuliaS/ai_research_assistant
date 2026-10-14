"""Validate citation provenance, not the truth of the claims being cited."""
import re
import logging
from typing import Any
from .source_registry import render_references

LINK = re.compile(r"\[([^\]\n]+)\]\(<?(https?://[^\s<>]+?)>?\)")
SOURCE_HEADING = re.compile(r"^#{1,6}\s+(Lähteet|Sources)\s*:?\s*$", re.MULTILINE)


def validate_citations(raw: str, sources: dict[str, dict[str, str]], *, require_evidence_notes: bool = False) -> tuple[bool, Any]:
    valid, result = _validate_citations(raw, sources, require_evidence_notes=require_evidence_notes)
    if not valid:
        # Messages below are fixed validation instructions, never model/provider text.
        logging.getLogger(__name__).warning("Report validation rejected: %s", result)
    return valid, result


def _validate_citations(raw: str, sources: dict[str, dict[str, str]], *, require_evidence_notes: bool = False) -> tuple[bool, Any]:
    try:
        raw = render_references(raw, sources)
    except ValueError:
        return False, "Use only registered source IDs such as [S1]."
    heading = SOURCE_HEADING.search(raw)
    if not heading:
        return False, "Add a final section named exactly '## Lähteet' or '## Sources'."
    body = raw[:heading.start()]
    bibliography = raw[heading.end():]
    body_urls = {url for _, url in LINK.findall(body)}
    all_urls = {url for _, url in LINK.findall(raw)}
    if len(body_urls) < 2:
        return False, "Cite at least two distinct retrieved sources inline beside factual claims. Use [title](https://...) links."
    if all_urls - sources.keys():
        return False, "Use only exact URLs from citation_sources returned by the search tool. Do not invent URLs."
    # Also reject bare URLs and Markdown reference links not observed in this run.
    remaining = LINK.sub("", raw)
    if re.search(r"https?://", remaining):
        return False, "Format all URLs as [title](URL) links using exact retrieved URLs."
    finnish = heading.group(1) == "Lähteet"
    notes = {}
    current_url = None
    for line in bibliography.splitlines():
        match = LINK.search(line)
        if match:
            current_url = match.group(2)
            notes[current_url] = line[match.end():].strip(" —–-\t")
        elif current_url and line[:1].isspace() and line.strip():
            notes[current_url] += " " + line.strip()
        elif line.strip():
            current_url = None
    if require_evidence_notes:
        evidence_heading = "## Näytön vahvuus ja puutteet" if finnish else "## Evidence strength and gaps"
        if evidence_heading not in body:
            body += (f"\n\n{evidence_heading}\n\n"
                     + ("Raportista puuttuu erillinen näytön arviointi. Päätelmien vahvuutta ei ole vahvistettu."
                        if finnish else "The report lacks a separate evidence assessment. The strength of its conclusions has not been established."))
    entries = []
    for url in sorted(all_urls):
        source = sources[url]
        title = re.sub(r"[\[\]<>\r\n]", "", source["title"])
        label = "Haettu" if finnish else "Retrieved"
        entries.append(f"- [{title}]({url}) — {label} {source['retrieved']}.")
        published = source.get('published_at')
        entries[-1] += ((f" Julkaistu {published}." if published else " Julkaisupäivä ei tiedossa.")
                        if finnish else (f" Published {published}." if published else " Publication date unknown."))
        read = source.get("page_status") == "retrieved" and bool(source.get("page_text"))
        entries[-1] += ((" Sivulta poimittu rajattu teksti." if read else " Vain hakutuloskatkelma; sivusisältöä ei saatu tai luettu.")
                        if finnish else (" Bounded page text retrieved." if read else "Search snippet only; page content was unavailable or not read."))
        if notes.get(url):
            entries[-1] += f" {notes[url]}"
        elif require_evidence_notes:
            entries[-1] += (" Lähteen käyttötarkoituksen ja rajoitusten arvio puuttuu."
                            if finnish else "An assessment of this source's purpose and limitations is missing.")
        reasons = list(dict.fromkeys(item.get("reason", "").strip()
                                     for item in source.get("selections", []) if item.get("reason", "").strip()))
        if reasons:
            # Selection is the agent's stated rationale, not an independent
            # reliability rating. Keep it separate from evidence limitations.
            reason = re.sub(r"[\[\]<>\r\n]", " ", reasons[0])
            entries[-1] += (" Valintaperuste: " if finnish else "Selection rationale: ") + reason
    if len(body_urls) < 5:
        entries.append("\n**Suppea lähdepohja:** raportissa on alle viisi tekstissä käytettyä lähdettä. Tarkista erityisesti, löytyykö väitteille riippumatonta näyttöä."
                       if finnish else "\n**Limited source base:** fewer than five sources are cited inline. Check whether independent evidence supports the claims.")
    note = (
        "Aineisto sisältää hakutuloskatkelmia ja erikseen merkittyjen lähteiden rajattuja sivutekstejä. "
        "Kartoitus ei ole kattava: löydetyt toimijat eivät ole alueen kokonaismäärä, "
        "eikä hausta puuttuminen osoita palvelun puuttumista. "
        "Lähteen löytyminen tai sivutekstin lukeminen ei takaa väitteiden oikeellisuutta."
        if finnish else
        "Evidence consists of search snippets and bounded page extracts where explicitly marked. "
        "This is not an exhaustive market census: providers found are not the area's total, "
        "and missing search results do not establish absence. Retrieval does not verify every claim."
    )
    return True, f"{body.rstrip()}\n\n## {heading.group(1)}\n\n" + "\n".join(entries) + f"\n\n{note}\n"
