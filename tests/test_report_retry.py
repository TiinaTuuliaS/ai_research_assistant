import os
import unittest
from unittest.mock import patch

from crewai import Agent

from src.ai_research_assistant.crew import AiResearchAssistant


class ReportRetryTests(unittest.TestCase):
    def test_actual_task_retry_receives_evidence_and_reviewed_draft(self):
        contexts = []
        repaired = ("Hinta [One](https://one.test/menu). "
                    "Valikoima [Two](https://two.test/products).\n\n## Lähteet\n")
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}), \
             patch("src.ai_research_assistant.crew.review_output",
                   side_effect=lambda raw, **kwargs: (True, raw.replace("Unsupported claim", "Evidence is limited"))):
            assistant = AiResearchAssistant()
            assistant.search_tool.sources.update({
                "https://one.test/menu": {"title": "One", "snippet": "Hinta 12 euroa", "retrieved": "2026-10-07"},
                "https://two.test/products": {"title": "Two", "snippet": "Valikoimassa takkeja", "retrieved": "2026-10-07"},
            })

            def execute(agent, task, context=None, tools=None):
                contexts.append(context)
                return "Unsupported claim\n\n## Lähteet\n" if len(contexts) == 1 else repaired

            with patch.object(Agent, "execute_task", execute):
                output = assistant.report_task().execute_sync(context="Original agent context")
            self.assertEqual(len(contexts), 2)
            self.assertIn("https://one.test/menu", contexts[1])
            self.assertIn("Hinta 12 euroa", contexts[1])
            self.assertIn("https://two.test/products", contexts[1])
            self.assertIn("Evidence is limited", contexts[1])
            self.assertNotIn("Unsupported claim", contexts[1])
            self.assertIn("Haettu 2026-10-07", output.raw)

    def test_review_removed_claim_and_link_do_not_reenter_retry_context(self):
        from crewai.tasks.task_output import TaskOutput

        raw = "Unsupported claim [One](https://one.test/menu).\n\n## Sources\n"
        reviewed = "Evidence is limited.\n\n## Sources\n"
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}), \
             patch("src.ai_research_assistant.crew.review_output", return_value=(True, reviewed)):
            assistant = AiResearchAssistant()
            output = TaskOutput(description="Report", agent="Writer", raw=raw)
            valid, feedback = assistant.check_sources(output)
            self.assertFalse(valid)
            self.assertEqual(output.raw, reviewed)
            self.assertNotIn("Unsupported claim", feedback)
            self.assertNotIn("https://one.test/menu", output.raw)

    def test_repair_feedback_still_rejects_missing_citations(self):
        from crewai.tasks.task_output import TaskOutput

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}), \
             patch("src.ai_research_assistant.crew.review_output", return_value=(True, "No citations\n\n## Sources\n")):
            assistant = AiResearchAssistant()
            valid, feedback = assistant.check_sources(TaskOutput(description="Report", agent="Writer", raw="Draft"))
            self.assertFalse(valid)
            self.assertIn("at least two", feedback)
            self.assertIn('"retrieved_evidence": []', feedback)
