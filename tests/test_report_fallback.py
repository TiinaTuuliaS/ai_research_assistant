from tests.test_analysis_result import analysis_fixture
import os
import unittest
from unittest.mock import patch

from src.ai_research_assistant.report_fallback import compose_fallback
from src.ai_research_assistant.research_result import ResearchFinding, ResearchResult, render_research
from src.ai_research_assistant.evidence import filter_excerpt_findings
from src.ai_research_assistant.trend_result import TrendResult


class FallbackTests(unittest.TestCase):
    def sources(self):
        return {"https://example.test/": {"title": "Palvelut", "snippet": "ORIGINAL SOURCE WORDING",
            "research_findings": [{"summary": "Yritys tarjoaa ryhmäliikuntaa.", "source": "https://example.test/",
                "limitations": ["Asiakasmäärä ei selviä."], "evidence_kind": "offering"}]}}

    def test_mode_specific_report_without_model_calls_or_source_quotes(self):
        for mode in ("competition", "market"):
            for language in ("suomi", "english"):
                text = compose_fallback({"research_type": mode, "language": language}, self.sources(), [])
                self.assertIn("Yritys tarjoaa ryhmäliikuntaa", text)
                self.assertIn("https://example.test/", text)
                self.assertNotIn("ORIGINAL SOURCE WORDING", text)
                self.assertIn("Rajattu raportti" if language == "suomi" else "Limited report", text)

    def test_accepted_recommendation_is_preserved_even_if_negative(self):
        accepted = [{"stage": "strategy_task", "text": "Suositus: lykkää toteutusta. Hintaero on epäedullinen [Hinta](https://example.test/)."}]
        text = compose_fallback({"research_type": "market"}, self.sources(), accepted)
        self.assertIn("lykkää toteutusta", text)

    def test_no_evidence_is_failure_not_a_fake_report(self):
        self.assertIsNone(compose_fallback({}, {}, []))
        self.assertIsNone(compose_fallback({}, {"https://example.test/": {"snippet": "Raw unreviewed"}}, []))
        self.assertIsNone(compose_fallback({}, {}, [{"stage": "strategy_task", "text": "[Invented](https://bad.test/)"}]))

    def test_server_attaches_source_and_renderer_never_exposes_quotes_or_rejections(self):
        finding = ResearchFinding(title="Tarjonta", summary="Omin sanoin kirjoitettu havainto.",
            source="https://example.test/", relevance=8, evidence_kind="offering",
            entity=None, area=None, period=None, limitations=["Kysyntä ei selviä."])
        result, excluded = filter_excerpt_findings(ResearchResult(topic="Test", findings=[finding]), self.sources())
        self.assertEqual(result.findings[0].evidence_excerpt, "ORIGINAL SOURCE WORDING")
        self.assertNotIn("evidence_excerpt", ResearchFinding.model_json_schema()["properties"])
        self.assertNotIn("evidence_excerpt", result.findings[0].model_dump())
        rendered = render_research(result, excluded=["INTERNAL REJECTION"])
        self.assertIn("Omin sanoin", rendered)
        self.assertNotIn("ORIGINAL", rendered)
        self.assertNotIn("INTERNAL", rendered)

    def test_writer_failure_returns_report_and_completed_writer_progress(self):
        from crewai import Agent
        from src.api import generate_report
        from src.ai_research_assistant.crew import AiResearchAssistant
        updates = []
        saved = {}
        def execute(agent, task, context=None, tools=None):
            if task.name == "research_task":
                agent.tools[0].sources.update(self.sources())
                return ResearchResult(topic="Test", findings=[ResearchFinding(title="Tarjonta",
                    summary="Yritys tarjoaa ryhmäliikuntaa.", source="S1", supporting_text="ORIGINAL SOURCE WORDING", relevance=8,
                    evidence_kind="offering", entity=None, area=None, period=None,
                    limitations=["Kysyntä ei selviä."])])
            if task.name == "report_task":
                return "REJECTED WRITER DRAFT"
            if task.name == "trend_task":
                return TrendResult(topic="Test", findings=[])
            return analysis_fixture(mode="market", ids=["F1"])
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}), \
             patch.object(Agent, "execute_task", execute), \
             patch("src.ai_research_assistant.crew.assess_findings", side_effect=lambda result, *args: (result, [])), \
             patch("src.ai_research_assistant.crew.review_output", side_effect=lambda raw, **kwargs:
                   (False, "SCOPE_REJECTION") if kwargs.get("final_report") else (True, raw)):
            result = generate_report("Test", "suomi", research_type="market", progress=lambda *args: updates.append(args),
                                     checkpoint=lambda **values: saved.update(values))
        self.assertIn("Rajattu raportti", result)
        self.assertIn("Perusteltu ehdollinen näkemys", result)
        self.assertTrue(any(i == 2 and state == "completed" and text == result for i, state, text in updates))
        self.assertEqual(saved["draft"], "REJECTED WRITER DRAFT")
        self.assertIn("SCOPE_REJECTION", saved["feedback"])
