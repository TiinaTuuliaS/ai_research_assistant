"""Compose a clearly limited report from accepted outputs, never rejected drafts."""
import re
from .evidence import evidence_ledger, accepted_sources
from .citations import LINK
from .quality import remove_editor_instructions
from .trend_result import attach_trend_evidence
from .source_registry import render_references


def compose_fallback(brief, sources, accepted):
    findings = evidence_ledger(sources)
    stages = {item.get("stage"): item["text"] for item in accepted if item.get("text")}
    if not findings and not any(stages.get(key) for key in ("trend_task", "analysis_task", "strategy_task")):
        return None
    fi = brief.get("language") != "english"
    mode = brief.get("research_type", "market")
    conclusions = {
        "demand": ("Idean kysyntää ei tämän rajatun koosteen perusteella voi vahvistaa eikä sulkea pois. "
                   "Laajaa toteutuspäätöstä ei kannata perustaa yksin tähän aineistoon.",
                   "This limited report cannot confirm or rule out demand. A substantial commitment should not rely on this evidence alone."),
        "competition": ("Aineisto auttaa vertaamaan löydettyjä vaihtoehtoja, mutta ei yksin osoita ratkaisusi kilpailuetua. "
                        "Erottautumista koskeva päätös jää ehdolliseksi, kunnes vertailtava ero on vahvistettu.",
                        "The evidence helps compare alternatives but does not alone establish a competitive advantage. A differentiation decision remains conditional on a verified difference."),
        "market": ("Aineistosta voi muodostaa rajatun tilannekuvan. Sen perusteella ei pidä olettaa koko markkinan suuntaa tai kokoa. "
                   "Päätöksessä kannattaa erottaa tässä kuvatut havainnot koko markkinaa koskevista oletuksista.",
                   "The evidence provides a limited snapshot, not the size or direction of the whole market. Base decisions on the observations below rather than assuming they describe the entire market."),
    }
    conclusion = stages.get("strategy_task") or stages.get("analysis_task") or conclusions[mode][0 if fi else 1]
    sections = ["## " + ("Päätelmä" if fi else "Conclusion"), conclusion,
                ("**Rajattu raportti:** viimeistely ei onnistunut. Tämä kooste sisältää vain valmistuneet, tarkistetut tulokset. "
                 "Puuttuva analyysi ei tarkoita kielteistä arviota ideasta."
                 if fi else "**Limited report:** final synthesis failed. This compilation contains only completed, reviewed results. Missing analysis is not evidence against the idea."),
                ]
    if findings:
        sections.append("## " + ("Ratkaisevat havainnot" if fi else "Key findings"))
    # Summaries are the researcher's reviewed paraphrases. Never publish source_passage/page_text.
    for finding in findings[:6]:
        sections.append(f"- {finding['summary']} [" + ("Lähde" if fi else "Source") + f"]({finding['source']})")
    if stages.get("analysis_task") and stages.get("strategy_task"):
        sections.extend(["## " + ("Perustelut" if fi else "Reasoning"), stages["analysis_task"]])
    elif not findings and stages.get("trend_task"):
        sections.append(stages["trend_task"])
    limits = list(dict.fromkeys(limit for finding in findings for limit in finding.get("limitations", [])))
    sections.extend(["## " + ("Näytön vahvuus ja puutteet" if fi else "Evidence strength and gaps"),
                     " ".join(limits[:5]) or ("Loppuraportin viimeistely ei onnistunut. Tämä kooste ei korvaa kattavaa tutkimusta; päätelmä on rajattu tallennettuun aineistoon."
                         if fi else "Final synthesis did not succeed. This compilation is limited to the saved evidence and does not replace a comprehensive study.")])
    body = remove_editor_instructions("\n\n".join(sections))
    body = attach_trend_evidence(body, sources, brief.get("language", "suomi"))
    try:
        body = render_references(body, sources, brief.get('language', 'suomi'))
    except ValueError:
        return None
    # Earlier stages may use plain URLs. Normalize them before the same
    # registered-source check; never treat an unregistered URL as evidence.
    body = re.sub(r"(?<!\]\()https?://[^\s<>\[\]()]+",
                  lambda m: "[" + ("Lähde" if fi else "Source") + "](" + m.group().rstrip(".,;") + ")" +
                  m.group()[len(m.group().rstrip(".,;")):], body)
    # Fail closed if accepted text unexpectedly contains an unregistered link.
    normalized = {url.rstrip("/"): url for url in sources}
    for label, url in LINK.findall(body):
        if url not in sources:
            original = normalized.get(url.rstrip("/"))
            if not original:
                return None
            body = body.replace(f"]({url})", f"]({original})")
    urls = list(dict.fromkeys(url for _, url in LINK.findall(body)))
    if any("research_findings" in source or "trend_findings" in source for source in sources.values()):
        if set(urls) - accepted_sources(sources).keys():
            return None
    if not urls:
        return None
    return body + "\n\n## " + ("Lähteet" if fi else "Sources") + "\n\n" + "\n".join(
        "- [" + re.sub(r"[\[\]<>\r\n]", "", sources[url].get("title") or "Source") + f"]({url})" for url in urls)
