from tests.test_analysis_result import analysis_fixture
from src.ai_research_assistant.analysis_result import AnalysisResult
import os
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from src.ai_research_assistant.research_result import ResearchFinding, ResearchResult, render_research, NoEvidenceError
from src.ai_research_assistant.trend_result import TrendResult, TrendFinding


class ResearchResultTests(unittest.TestCase):
    def test_bad_excerpt_after_retry_does_not_stop_three_stage_workflow(self):
        from crewai import Agent
        from src.ai_research_assistant.crew import AiResearchAssistant
        for keep_valid in (True, False):
            with self.subTest(keep_valid=keep_valid), \
                 patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}), \
                 patch("src.ai_research_assistant.crew.assess_findings", side_effect=lambda result, *args: (result, [])), \
                 patch("src.ai_research_assistant.crew.review_output", side_effect=lambda raw, **kwargs: (True, raw)):
                assistant = AiResearchAssistant()
                calls = []
                def execute(agent, task, context=None, tools=None):
                    calls.append(task.name)
                    if task.name == "research_task":
                        assistant.search_tool.sources.update({url: {"title": "Testilähde", "retrieved": "2026-10-08", "snippet": "Lähteessä mainittu palvelu."}
                            for url in ("https://example.test", "https://two.test/")})
                        bad = ResearchFinding(**{**self.finding(), "title": "Varmistamaton väite",
                            "summary": "Tätä väitettä ei saa välittää.", "source": "S999", "supporting_text": "Tuntematon", "period": None})
                        return ResearchResult(topic="Test", findings=([ResearchFinding(**self.wire_finding())] if keep_valid else []) + [bad])
                    self.assertNotIn("Tätä väitettä ei saa välittää", context)
                    self.assertNotIn("Havainto jätettiin pois", context)
                    if task.name == "trend_task":
                        return TrendResult(topic="Test", findings=[])
                    if task.name == "report_task":
                        return "Aineisto ei osoita kysyntää [Yksi](https://example.test) [Kaksi](https://two.test/)\n\n## Lähteet\n"
                    return analysis_fixture(ids=["F1"] if keep_valid else [])
                with patch.object(Agent, "execute_task", execute):
                    if not keep_valid:
                        with self.assertRaises(NoEvidenceError):
                            assistant.crew().kickoff(inputs={"topic": "Test", "language": "suomi", "current_year": "2026"})
                        self.assertEqual(calls, ["research_task"])
                        continue
                    result = assistant.crew().kickoff(inputs={"topic": "Test", "language": "suomi", "current_year": "2026"})
                self.assertEqual(calls.count("research_task"), 1)
                self.assertEqual(len(result.tasks_output), 3)
                self.assertEqual(len(result.tasks_output[0].pydantic.findings), int(keep_valid))
                self.assertIn("Aineisto ei osoita", result.raw)

    def test_real_guardrail_retry_accepts_pydantic_agent_result(self):
        from crewai import Agent, Task
        from src.ai_research_assistant.crew import AiResearchAssistant
        calls = []
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}), \
             patch("src.ai_research_assistant.crew.assess_findings", side_effect=lambda result, *args: (result, [])):
            assistant = AiResearchAssistant()
            task = assistant.research_task()
            assistant.search_tool.sources["https://example.test"] = {"snippet": "Lähteessä mainittu palvelu."}
            def execute(agent, task, context=None, tools=None):
                calls.append(context)
                values = self.wire_finding()
                if len(calls) == 1:
                    return "bad"
                return ResearchResult(topic="Test", findings=[ResearchFinding(**values)])
            with patch.object(Agent, "execute_task", execute), patch.object(Task, "_export_output",
                    side_effect=lambda raw: (None, None) if raw == "bad" else (ResearchResult.model_validate_json(raw), None)):
                output = task.execute_sync()
            self.assertEqual(len(calls), 2)
            self.assertIn("ResearchResult", calls[1])
            self.assertIsInstance(output.pydantic, ResearchResult)
            self.assertIn("Lähteessä mainittu palvelu.", output.raw)
            self.assertNotIn("Katkelma jota", output.raw)

    def wire_finding(self):
        return {**self.finding(), "source": "S1", "period": None,
                "supporting_text": "Lähteessä mainittu palvelu."}

    def finding(self):
        return dict(title="Tarjonta", summary="Lähteessä mainittu palvelu.",
                    source="https://example.test", relevance=8,
                    evidence_excerpt="Lähteessä mainittu palvelu.", evidence_kind="offering",
                    entity=None, area=None, period=None, limitations=["Käyttömäärä ei selviä."])

    def test_schema_rejects_invalid_values(self):
        for field, values in {"title": ["", "   "], "summary": [" "],
                              "source": ["not-a-url", "ftp://example.test/file"],
                              "relevance": [0, 11, 7.5, True, "8"]}.items():
            for value in values:
                with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                    ResearchFinding.model_validate({**self.finding(), field: value})
        with self.assertRaises(ValidationError):
            ResearchResult(topic=" ", findings=[])
        with self.assertRaises(ValidationError):
            ResearchFinding.model_validate({**self.finding(), "invented_field": True})

    def test_empty_findings_is_honest_and_rendered_clearly(self):
        result = ResearchResult(topic=" Test ", findings=[])
        self.assertEqual(result.topic, "Test")
        self.assertIn("ei löytynyt", render_research(result))

    def test_openai_schema_omits_uri_format_but_still_validates_urls(self):
        from openai.lib._pydantic import to_strict_json_schema

        schema = to_strict_json_schema(ResearchResult)
        source = schema["$defs"]["ResearchFinding"]["properties"]["source"]
        self.assertEqual(source["type"], "string")
        self.assertNotIn("format", source)
        for url in ("not-a-url", "ftp://example.test/file"):
            with self.subTest(url=url), self.assertRaises(ValidationError):
                ResearchResult.model_validate_json(ResearchResult(
                    topic="Test", findings=[ResearchFinding(**self.finding())]
                ).model_dump_json().replace("https://example.test/", url))

    def test_render_uses_registered_url_and_retains_score_meaning(self):
        result = ResearchResult(topic="Test", findings=[ResearchFinding(**self.finding())])
        text = render_research(result, sources={"https://example.test": {}})
        self.assertIn("[Lähde](https://example.test)", text)
        self.assertIn("8/10", text)
        self.assertIn("ei lähteen luotettavuutta", text)

    def test_real_crew_passes_validated_research_to_existing_context_and_progress(self):
        from crewai import Agent
        from src.ai_research_assistant.crew import AiResearchAssistant
        from src.ai_research_assistant.progress import track_tasks

        calls = []
        updates = []
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}), \
             patch("src.ai_research_assistant.crew.review_output", side_effect=lambda raw, **kwargs: (True, raw)), \
             patch("src.ai_research_assistant.crew.assess_findings", side_effect=lambda result, *args, **kwargs: (result, [])):
            assistant = AiResearchAssistant()
            crew = assistant.crew()

            def execute(agent, task, context=None, tools=None):
                calls.append((task.name, context))
                if task.name == "research_task":
                    assistant.search_tool.sources.update({url: {"title": "Source", "retrieved": "2026-10-07", "snippet": "Lähteessä mainittu palvelu."}
                                                         for url in ("https://example.test", "https://two.test/")})
                    assistant.search_tool.sources['https://two.test/']['snippet'] = 'Forecast 2026–2030'
                    return ResearchResult(topic="Test topic", findings=[ResearchFinding(**self.wire_finding())]).model_dump_json()
                if task.name == "report_task":
                    return "Answer [One](https://example.test) [Two](https://two.test/)\n\n## Sources\n"
                return analysis_fixture(topic="Test topic", ids=["F1"])

            def display_output(index, output):
                return assistant.accepted_outputs[index]["text"] if index < len(assistant.accepted_outputs) else output.raw
            with patch.object(Agent, "execute_task", execute), track_tasks(
                    crew, lambda *args: updates.append(args), display_output=display_output):
                result = crew.kickoff(inputs={"topic": "Test topic", "language": "suomi", "current_year": "2026"})
            self.assertIsInstance(result.tasks_output[0].pydantic, ResearchResult)
            self.assertIsInstance(result.tasks_output[1].pydantic, AnalysisResult)
            for name, context in calls:
                if name in ("trend_task", "analysis_task", "strategy_task", "report_task"):
                    self.assertIn("Lähteessä mainittu palvelu.", context)
                    self.assertIn("https://example.test", context)
                    self.assertIn('"relevance": 8', context)
                    self.assertIn('"supporting_text": "Lähteessä mainittu palvelu."', context)
                    self.assertNotIn("Lähteen tekstikohta:", context)
                    self.assertIn("Käyttömäärä ei selviä", context)
            research_update = next(output for index, status, output in updates if index == 0 and status == "completed")
            self.assertIn("### Tarjonta", research_update)
            self.assertFalse(research_update.startswith("{"))

    def test_crewai_raw_fallback_stops_before_next_agent(self):
        from crewai import Agent, Task
        from src.ai_research_assistant.crew import AiResearchAssistant
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}):
            crew = AiResearchAssistant().crew()
            with patch.object(Agent, "execute_task", return_value="Malformed result") as execute, \
                 patch.object(Task, "_export_output", return_value=(None, None)):
                with self.assertRaisesRegex(Exception, "ResearchResult"):
                    crew.kickoff(inputs={"topic": "Test", "language": "suomi", "current_year": "2026"})
                self.assertEqual(execute.call_count, 2)  # one bounded schema repair attempt

    def test_unretrieved_source_is_rejected(self):
        from crewai.tasks.task_output import TaskOutput
        from src.ai_research_assistant.crew import AiResearchAssistant
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}):
            assistant = AiResearchAssistant()
            output = TaskOutput(description="Test", agent="Researcher", raw="",
                                pydantic=ResearchResult(topic="Test", findings=[ResearchFinding(**self.finding())]))
            with self.assertRaises(NoEvidenceError):
                assistant.accept_research(output)
            self.assertEqual(output.pydantic.findings, [])
            self.assertNotIn("https://example.test", output.raw)
