import json
import unittest
from unittest.mock import Mock, patch

from src.ai_research_assistant.evidence import assess_findings, repair_excerpts, accepted_sources
from src.ai_research_assistant.research_result import ResearchFinding, ResearchResult
from src.ai_research_assistant.trend_result import TrendFinding, TrendResult
from src.ai_research_assistant.quality import review_output
from src.ai_research_assistant.report_fallback import compose_fallback


class EvidenceFlowTests(unittest.TestCase):
    def finding(self, **changes):
        values = dict(title="Paikallinen tarjonta", summary="Yritys huoltaa pyöriä Tampereella.",
            source="S1", supporting_text="Huollamme pyöriä Tampereella.", period_support="",
            evidence_kind="offering", entity="Huolto", area="Tampere", period=None,
            relevance=8, limitations=["Maksava kysyntä ei selviä."])
        return ResearchFinding(**{**values, **changes})

    def test_offering_check_does_not_receive_business_demand_question(self):
        sources = {"https://service.test/": {"source_id": "S1", "snippet": "Huollamme pyöriä Tampereella."}}
        reviewer = Mock()
        reviewer.call.return_value = {"assessments": [{"finding_id": "F1", "supported": True,
            "scope_supported": True, "single_source_supported": True, "reason": "Tarjonta on osoitettu."}]}
        result, _ = repair_excerpts(ResearchResult(topic="Pyörähuolto", findings=[self.finding()]), sources, reviewer)
        checked, _ = assess_findings(result, sources,
            {"goal": "Prove paying demand for my business", "research_type": "market", "language": "suomi"}, reviewer)
        self.assertEqual(len(checked.findings), 1)
        payload = json.loads(reviewer.call.call_args.args[0][1]["content"])
        self.assertEqual(payload["brief"], {"language": "suomi"})
        self.assertEqual(payload["findings"][0]["evidence_kind"], "offering")

    def test_dated_transfer_survives_passage_repair_without_losing_trend_fields(self):
        passage = "Helenin latausliiketoiminta siirtyi 1.9.2026 Plugitille."
        source = {"source_id": "S1", "snippet": passage}
        sources = {"https://transfer.test/": source}
        finding = TrendFinding(**self.finding(title="Omistajanvaihdos",
            summary="Helenin latausliiketoiminta siirtyi Plugitille syyskuussa 2026.",
            supporting_text="not a verbatim passage", period="1.9.2026", period_support="1.9.2026",
            entity="Helen", area="Suomi", evidence_kind="other").model_dump(exclude={"trend_kind", "local_relevance"}),
            trend_kind="observed_change", local_relevance="Toimija vaihtuu; ei osoita käyttöasteen kasvua.")
        repaired = finding.model_copy(update={"supporting_text": passage})
        reviewer = Mock()
        reviewer.call.side_effect = [TrendResult(topic="Lataus", findings=[repaired]),
            {"assessments": [{"finding_id": "F1", "supported": True, "scope_supported": True,
                              "single_source_supported": True, "reason": "Ajoitettu muutos."}]}]
        result, _ = repair_excerpts(TrendResult(topic="Lataus", findings=[finding]), sources, reviewer)
        result, _ = assess_findings(result, sources, {"language": "suomi"}, reviewer)
        self.assertIsInstance(result, TrendResult)
        self.assertEqual(result.findings[0].period, "1.9.2026")
        self.assertEqual(result.findings[0].trend_kind, "observed_change")
        self.assertEqual(source["finding_exclusions"][0]["stage"], "provenance")
        self.assertEqual(reviewer.call.call_count, 2)

    def test_invalid_repair_does_not_restore_unsupported_claim(self):
        finding = self.finding(supporting_text="invented")
        sources = {"https://service.test/": {"source_id": "S1", "snippet": "Huollamme pyöriä Tampereella."}}
        reviewer = Mock()
        reviewer.call.return_value = ResearchResult(topic="Test", findings=[finding])
        result, _ = repair_excerpts(ResearchResult(topic="Test", findings=[finding]), sources, reviewer)
        self.assertEqual(result.findings, [])
        reviewer.call.assert_called_once()

    def test_discarded_sources_cannot_reenter_quality_context_and_roles_are_explicit(self):
        sources = {"https://competitor.test/": {"source_id": "S1", "page_text": "unreviewed extras",
            "research_findings": [{"entity": "PAW BOUTIQUE", "summary": "Tarjoaa ilta-aikoja.",
                "supporting_text": "Yksityiset ajat klo 18 jälkeen.", "source": "https://competitor.test/"}]},
            "https://discarded.test/": {"snippet": "unverified market gap"}}
        reviewer = Mock()
        reviewer.call.return_value = {"issues": []}
        review_output("Ilta-ajat eivät yksin erota suunnitelmaasi kilpailijasta.", sources=sources,
            brief={"topic": "Uusi trimmaamo Espoossa", "research_type": "competition"}, previous=[], reviewer=reviewer)
        payload = json.loads(reviewer.call.call_args.args[0][1]["content"])
        self.assertNotIn("unverified market gap", json.dumps(payload))
        self.assertNotIn("unreviewed extras", json.dumps(payload))
        self.assertEqual(payload["subject_roles"]["external_entities"], ["PAW BOUTIQUE"])
        self.assertEqual(payload["subject_roles"]["user_proposal"], "Uusi trimmaamo Espoossa")
        self.assertEqual(list(accepted_sources(sources)), ["https://competitor.test/"])

    def test_fallback_has_no_empty_findings_heading_or_false_stage_failure(self):
        source = {"https://service.test/": {"title": "Palvelut"}}
        stages = [{"stage": "strategy_task", "text": "Ehdollinen suositus [Lähde](https://service.test/)."}]
        report = compose_fallback({}, source, stages)
        self.assertNotIn("## Ratkaisevat havainnot", report)
        self.assertNotIn("Kaikki analyysivaiheet eivät valmistuneet", report)

    def test_registered_but_rejected_source_cannot_reenter_via_a_citation(self):
        sources = {"https://discarded.test/": {"title": "Discarded", "research_findings": []}}
        reviewer = Mock()
        reviewer.call.return_value = {"issues": []}
        draft = "Väite [Lähde](https://discarded.test/)."
        ok, _ = review_output(draft, sources=sources, brief={}, previous=[], reviewer=reviewer)
        self.assertFalse(ok)
        self.assertIsNone(compose_fallback({}, sources, [{"stage": "analysis_task", "text": draft}]))
