import unittest
from unittest.mock import Mock, patch

from src.ai_research_assistant.evidence import assess_findings
from src.ai_research_assistant.research_result import ResearchFinding, ResearchResult
from src.ai_research_assistant.quality import review_output
from src.ai_research_assistant.report_fallback import compose_fallback


class ReportRegressionTests(unittest.TestCase):
    def test_optional_repair_failure_preserves_already_accepted_findings(self):
        finding = ResearchFinding(title="Palvelu", summary="Yritys tarjoaa koulutusta.",
            source="https://example.test/", relevance=8, evidence_kind="offering",
            entity=None, area=None, period=None, limitations=["Kysyntä ei selviä."],
            evidence_excerpt="Yritys tarjoaa koulutusta.")
        reviewer = Mock()
        reviewer.call.side_effect = [{"assessments": [
            {"finding_id": "F1", "supported": True, "scope_supported": True,
             "single_source_supported": True, "reason": "Tarjonta."},
            {"finding_id": "F2", "supported": False, "scope_supported": False,
             "single_source_supported": False, "reason": "Liian laaja päätelmä."}]},
            RuntimeError("Provider unavailable")]
        with patch("src.diagnostics.record_failure") as log:
            result, _ = assess_findings(ResearchResult(topic="Koulutus", findings=[finding,
                finding.model_copy(update={"summary": "Kaikki tarvitsevat koulutusta."})]),
                {"https://example.test/": {"snippet": "Yritys tarjoaa koulutusta."}}, {}, reviewer)
        self.assertEqual(result.findings, [finding])
        log.assert_called_once()

    def test_rejected_demand_conclusion_retains_verified_offering(self):
        url = "https://example.test/"
        finding = ResearchFinding(title="Palvelu", summary="Tarjonta osoittaa kysyntää.", source=url,
            relevance=8, evidence_kind="offering", entity=None, area=None, period=None,
            limitations=["Ostomäärä ei selviä."], evidence_excerpt="Yritys tarjoaa koulutusta.")
        narrow = finding.model_copy(update={"summary": "Yritys tarjoaa koulutusta."})
        sources = {url: {"snippet": "Yritys tarjoaa koulutusta."}}
        reviewer = Mock()
        reviewer.call.side_effect = [
            {"assessments": [{"finding_id": "F1", "supported": True, "scope_supported": False,
                "single_source_supported": True, "reason": "Tarjonta ei osoita kysyntää."}]},
            ResearchResult(topic="Koulutus", findings=[narrow]),
            {"assessments": [{"finding_id": "F1", "supported": True, "scope_supported": True,
                "single_source_supported": True, "reason": "Rajattu tarjontahavainto."}]},
        ]
        result, _ = assess_findings(ResearchResult(topic="Koulutus", findings=[finding]), sources, {}, reviewer)
        self.assertEqual(result.findings[0].summary, "Yritys tarjoaa koulutusta.")
        self.assertEqual(reviewer.call.call_count, 3)

    def test_editor_instruction_is_not_inserted_into_report(self):
        reviewer = Mock()
        reviewer.call.return_value = {"issues": [{"excerpt": "Väärä väite.",
            "correction": "Poista tämä lause, koska aiemmat agenttien väitteet eivät ole osa tätä luonnosta eikä niistä ole näyttöä."}]}
        ok, text = review_output("Yritys tarjoaa koulutusta. Väärä väite.", sources={}, brief={}, previous=[], reviewer=reviewer)
        self.assertTrue(ok)
        self.assertNotIn("Poista", text)
        self.assertNotIn("Väärä", text)
        self.assertIn("Yritys tarjoaa koulutusta.", text)

    def test_existing_editor_instruction_is_removed_from_fallback(self):
        url = "https://example.test/"
        stages = [{"stage": "analysis_task", "text":
            "Yritys tarjoaa koulutusta (" + url + "). Poista tämä lause, koska siitä ei ole näyttöä."}]
        text = compose_fallback({}, {url: {"title": "Koulutus"}}, stages)
        self.assertIn("Yritys tarjoaa koulutusta", text)
        self.assertNotIn("Poista tämä lause", text)

    def test_existing_markdown_links_are_not_wrapped_twice(self):
        url = "https://example.test/"
        stages = [{"stage": "analysis_task", "text": "[Koulutus](" + url + ")"}]
        text = compose_fallback({}, {url: {"title": "Koulutus"}}, stages)
        self.assertIn("[Koulutus](https://example.test/)", text)
        self.assertNotIn("[Koulutus]([", text)

    def test_fallback_accepts_registered_plain_urls_but_not_unknown_urls(self):
        url = "https://example.test/"
        stages = [{"stage": "analysis_task", "text": "Yritys tarjoaa koulutusta (" + url + ", 2026)."}]
        text = compose_fallback({}, {url: {"title": "Koulutus"}}, stages)
        self.assertIn("[Lähde](https://example.test/)", text)
        self.assertIsNone(compose_fallback({}, {}, stages))

