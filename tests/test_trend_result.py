import os
import unittest
from unittest.mock import Mock, patch

from pydantic import ValidationError
from src.ai_research_assistant.trend_result import TrendFinding, TrendResult, attach_trend_evidence
from src.ai_research_assistant.tools.search_tool import SourceSearchTool, SourceReadTool
from src.ai_research_assistant.evidence import evidence_ledger


class TrendTests(unittest.TestCase):
    def test_real_guardrail_retry_accepts_typed_trend_result(self):
        from crewai import Agent, Task
        from src.ai_research_assistant.crew import AiResearchAssistant
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}):
            assistant = AiResearchAssistant()
            task = assistant.trend_task()
            with patch.object(Agent, "execute_task", side_effect=["bad", TrendResult(topic="Test", findings=[])]), \
                 patch.object(Task, "_export_output", side_effect=lambda raw: (None, None) if raw == "bad" else
                              (TrendResult.model_validate_json(raw), None)):
                output = task.execute_sync()
        self.assertIsInstance(output.pydantic, TrendResult)
        self.assertEqual(output.pydantic.findings, [])
        self.assertNotIn('"findings"', output.raw)

    def finding(self):
        return TrendFinding(title="Markkinaennuste", summary="Julkaisija ennustaa 5,6 prosentin vuosikasvua.",
            source="https://forecast.test/", relevance=8, evidence_kind="other", entity="Julkaisija",
            area="Maailma", period="2026–2030", limitations=["Ei osoita paikallista kysyntää."],
            trend_kind="forecast", local_relevance="Vertailutausta; ei ennuste Tampereelle.")

    def test_schema_requires_trend_classification_and_scope(self):
        for key in ("source", "area", "period", "trend_kind", "local_relevance"):
            values = self.finding().model_dump()
            del values[key]
            with self.subTest(key=key), self.assertRaises(ValidationError):
                TrendFinding.model_validate(values)

    def test_real_task_reads_evidence_and_checkpoints_typed_forecast(self):
        from crewai import Agent
        from src.ai_research_assistant.crew import AiResearchAssistant
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}):
            assistant = AiResearchAssistant()
            assistant.brief = {"language": "suomi"}
            assistant.checkpoint = Mock()
            assistant.search_tool.sources["https://forecast.test/"] = {
                "url": "https://forecast.test/", "title": "Ennuste", "retrieved": "2026-10-14",
                "snippet": "Forecast", "page_status": "not_checked"}
            assistant.reviewer = Mock()
            assistant.reviewer.call.return_value = {"assessments": [{"finding_id": "F1",
                "supported": True, "scope_supported": True, "single_source_supported": True,
                "reason": "Ennuste on rajattu lähteen alueeseen ja ajankohtaan."}]}
            finding = self.finding().model_copy(update={'source': 'S1',
                'supporting_text': 'Forecast 5.6% global 2026–2030', 'period_support': '2026–2030'})
            with patch.object(Agent, "execute_task", return_value=TrendResult(topic="Test", findings=[finding])), \
                 patch("src.ai_research_assistant.tools.search_tool.read_page", return_value={
                     "page_status": "retrieved", "page_text": "Forecast 5.6% global 2026–2030"}) as read:
                output = assistant.trend_task().execute_sync()
            read.assert_called_once()
            self.assertIsInstance(output.pydantic, TrendResult)
            for value in ("Ennuste", "Maailma", "2026–2030", "https://forecast.test/"):
                self.assertIn(value, output.raw)
            saved = assistant.checkpoint.call_args.kwargs["sources"]
            self.assertEqual(evidence_ledger(saved)[0]["trend_kind"], "forecast")
            self.assertEqual(evidence_ledger(saved)[0]["finding_id"], "T1")
            self.assertIn("trend_kind", assistant.reviewer.call.call_args.args[0][1]["content"])
            report = "## Vastaus\nRajattu arvio.\n\n## Lähteet\n"
            final = attach_trend_evidence(report, saved)
            for value in ("Ennuste", "Maailma", "2026–2030", "https://forecast.test/"):
                self.assertIn(value, final)
            self.assertEqual(attach_trend_evidence(final, saved), final)

    def test_source_selection_survives_failed_read_and_repeat_search(self):
        from crewai_tools import SerperDevTool
        search = SourceSearchTool()
        url = "https://authority.test/"
        search.sources[url] = {"url": url, "page_status": "not_checked"}
        reader = SourceReadTool(search, "trend_task")
        with patch("src.ai_research_assistant.tools.search_tool.read_page", return_value={"page_status": "unavailable"}):
            reader._run([url], purpose="Vastuut", reason="Selvitetään asiakkaan ja kunnan vastuut.")
        with patch.object(SerperDevTool, "_run", return_value={"organic": [{"link": url, "title": "Vastuut"}]}):
            search._run(search_query="vastuut")
        self.assertEqual(search.sources[url]["selections"], [{"purpose": "Vastuut",
            "reason": "Selvitetään asiakkaan ja kunnan vastuut.", "stage": "trend_task"}])
        self.assertEqual(search.sources[url]["page_status"], "unavailable")

