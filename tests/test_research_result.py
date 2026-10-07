import os
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from src.ai_research_assistant.research_result import ResearchFinding, ResearchResult, render_research


class ResearchResultTests(unittest.TestCase):
    def finding(self):
        return dict(title="Tarjonta", summary="Lähteessä mainittu palvelu.",
                    source="https://example.test", relevance=8)

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
             patch("src.ai_research_assistant.crew.review_output", side_effect=lambda raw, **kwargs: (True, raw)):
            assistant = AiResearchAssistant()
            crew = assistant.crew()

            def execute(agent, task, context=None, tools=None):
                calls.append((task.name, context))
                if task.name == "research_task":
                    assistant.search_tool.sources.update({url: {"title": "Source", "retrieved": "2026-10-07"}
                                                         for url in ("https://example.test", "https://two.test/")})
                    return ResearchResult(topic="Test topic", findings=[ResearchFinding(**self.finding())]).model_dump_json()
                if task.name == "report_task":
                    return "Answer [One](https://example.test) [Two](https://two.test/)\n\n## Sources\n"
                return "Stage output"

            with patch.object(Agent, "execute_task", execute), track_tasks(crew, lambda *args: updates.append(args)):
                result = crew.kickoff(inputs={"topic": "Test topic", "language": "suomi", "current_year": "2026"})
            self.assertIsInstance(result.tasks_output[0].pydantic, ResearchResult)
            for name, context in calls:
                if name in ("trend_task", "analysis_task"):
                    self.assertIn("Lähteessä mainittu palvelu.", context)
                    self.assertIn("https://example.test", context)
                    self.assertIn("8/10", context)
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
                with self.assertRaisesRegex(ValueError, "ResearchResult"):
                    crew.kickoff(inputs={"topic": "Test", "language": "suomi", "current_year": "2026"})
                self.assertEqual(execute.call_count, 1)

    def test_unretrieved_source_is_rejected(self):
        from crewai.tasks.task_output import TaskOutput
        from src.ai_research_assistant.crew import AiResearchAssistant
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}):
            assistant = AiResearchAssistant()
            output = TaskOutput(description="Test", agent="Researcher", raw="",
                                pydantic=ResearchResult(topic="Test", findings=[ResearchFinding(**self.finding())]))
            with self.assertRaisesRegex(ValueError, "verkkohaku"):
                assistant.accept_research(output)
