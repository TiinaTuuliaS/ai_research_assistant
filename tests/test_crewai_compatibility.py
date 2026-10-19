import os
import unittest
from unittest.mock import patch

from crewai import Agent, Task
from pydantic import ValidationError

from src.ai_research_assistant.crew import AiResearchAssistant
from src.ai_research_assistant.research_result import ResearchResult
from src.ai_research_assistant.research_result import ResearchFinding
from src.ai_research_assistant.trend_result import TrendResult


class CrewAICompatibilityTests(unittest.TestCase):
    def test_bracketed_id_and_exact_registered_url_do_not_require_paid_retry(self):
        from crewai.tasks.task_output import TaskOutput
        values = dict(title='Offering', summary='Company offers repairs.', relevance=8,
            supporting_text='We offer repairs.', evidence_kind='offering', entity=None, area=None,
            period=None, limitations=['Demand unknown.'])
        self.assertEqual(ResearchFinding(source='[S1]', **values).source, 'S1')
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test', 'SERPER_API_KEY': 'test'}):
            assistant = AiResearchAssistant()
            assistant.search_tool.sources['https://example.test/'] = {'snippet': 'We offer repairs.'}
            finding = ResearchFinding(source='https://example.test/', **values)
            output = TaskOutput(description='Test', agent='Researcher', raw='', pydantic=ResearchResult(topic='Test', findings=[finding]))
            self.assertTrue(assistant.check_research(output)[0])
            self.assertEqual(output.pydantic.findings[0].source, 'S1')

    def test_converter_validation_error_uses_bounded_retry_for_both_structured_tasks(self):
        try:
            ResearchResult.model_validate({'topic': 'Test', 'findings': [{'source': '[S1]'}]})
        except ValidationError as exc:
            conversion_error = exc
        for method, schema in [('research_task', ResearchResult)]:
            with self.subTest(task=method), patch.dict(os.environ, {'OPENAI_API_KEY': 'test', 'SERPER_API_KEY': 'test'}):
                assistant = AiResearchAssistant()
                task = getattr(assistant, method)()
                task.callback = None  # Conversion contract only; empty evidence is rejected by the application callback.
                with patch.object(Agent, 'execute_task', side_effect=['invalid structure', schema(topic='Test', findings=[])]) as execute, \
                     patch.object(Task, '_export_output', side_effect=conversion_error):
                    output = task.execute_sync()
                self.assertEqual(execute.call_count, 2)
                self.assertIsInstance(output.pydantic, schema)
                self.assertEqual(output.pydantic.findings, [])
