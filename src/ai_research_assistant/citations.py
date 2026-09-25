"""Validate citation provenance, not the truth of the claims being cited."""
import re
from typing import Any

LINK = re.compile(r"\[([^\]\n]+)\]\(<?(https?://[^\s<>]+?)>?\)")
SOURCE_HEADING = re.compile(r"^##\s+(Lähteet|Sources)\s*$", re.MULTILINE)


def validate_citations(raw: str, sources: dict[str, dict[str, str]]) -> tuple[bool, Any]:
    heading = SOURCE_HEADING.search(raw)
    if not heading:
        return False, "Add a final section named exactly '## Lähteet' or '## Sources'."
    body = raw[:heading.start()]
    bibliography = raw[heading.end():]
    body_urls = {url for _, url in LINK.findall(body)}
    listed_urls = {url for _, url in LINK.findall(bibliography)}
    all_urls = {url for _, url in LINK.findall(raw)}
    if len(body_urls) < 2:
        return False, "Cite at least two distinct retrieved sources inline beside factual claims. Use [title](https://...) links."
    if not body_urls.issubset(listed_urls):
        return False, "Include every inline citation in the final sources section."
    if all_urls - sources.keys():
        return False, "Use only exact URLs from citation_sources returned by the search tool. Do not invent URLs."
    # Also reject bare URLs and Markdown reference links not observed in this run.
    remaining = LINK.sub("", raw)
    if re.search(r"https?://", remaining):
        return False, "Format all URLs as [title](URL) links using exact retrieved URLs."
    finnish = heading.group(1) == "Lähteet"
    entries = []
    for url in sorted(all_urls):
        source = sources[url]
        title = re.sub(r"[\[\]<>\r\n]", "", source["title"])
        label = "Haettu" if finnish else "Retrieved"
        entries.append(f"- [{title}]({url}) — {label} {source['retrieved']}.")
    note = (
        "Lähteet perustuvat verkkohakujen hakutuloskatkelmiin. Kokonaisia sivuja ei ole tarkistettu. "
        "Linkkien alkuperä on tarkistettu hakutuloksista; se ei takaa väitteiden oikeellisuutta."
        if finnish else
        "Sources are based on web search snippets; full pages were not reviewed. "
        "Links were checked against search results; this does not verify every claim."
    )
    return True, f"{body.rstrip()}\n\n## {heading.group(1)}\n\n" + "\n".join(entries) + f"\n\n{note}\n"
