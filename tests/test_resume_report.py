import os
import unittest
from unittest.mock import patch
from src.api import resume_report, new_steps
from src.ai_research_assistant.report_repair import ReportEdit, ReportRepair, apply_repair


class ResumeReportTests(unittest.TestCase):
    def test_only_writer_runs_with_stored_sources_and_existing_guardrail(self):
        from crewai import Agent
        calls, progress, checkpoints = [], [], []
        sources = {url: {"title": "Source", "retrieved": "2026-10-07", "snippet": "Observed offering"}
                   for url in ("https://one.test/", "https://two.test/")}
        steps = new_steps()
        for step in steps[:4]:
            step.update(status="completed", output="Stored finding {literal braces}")
        def execute(agent, task, context=None, tools=None):
            calls.append(task)
            return ReportRepair(edits=[ReportEdit(original="Finding one.", replacement="Finding one [One](https://one.test/)."),
                                       ReportEdit(original="Finding two.", replacement="Finding two [Two](https://two.test/).")]).model_dump_json()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}), \
             patch.object(Agent, "execute_task", execute), \
             patch("src.ai_research_assistant.crew.review_output", side_effect=lambda raw, **kwargs: (True, raw)), \
             patch("src.ai_research_assistant.tools.search_tool.SourceSearchTool._run") as search:
            result = resume_report({"topic": "Test", "language": "suomi", "current_year": "2026"}, sources, steps,
                                   lambda *args: progress.append(args), lambda **kwargs: checkpoints.append(kwargs),
                                   "Finding one. Finding two.\nKeep this conclusion.\n\n## Sources\n", "Missing inline citations")
        self.assertEqual(len(calls), 1)
        self.assertIn("Stored finding {literal braces}", calls[0].description)
        self.assertIn("https://one.test/", calls[0].description)
        self.assertIn("Retrieved 2026-10-07", result)
        self.assertIn("Keep this conclusion.", result)
        self.assertIn("Missing inline citations", calls[0].description)
        self.assertIn("Finding one. Finding two.", calls[0].description)
        self.assertTrue(any(index == 4 and state == "completed" for index, state, _ in progress))
        self.assertTrue(checkpoints)
        search.assert_not_called()

    def test_exact_edits_preserve_other_text_and_reject_ambiguous_or_overlapping_edits(self):
        draft = "First claim.\nSecond claim.\nKeep this conclusion."
        result = apply_repair(draft, ReportRepair(edits=[ReportEdit(original="First claim.", replacement="Limited evidence.")]))
        self.assertEqual(result, "Limited evidence.\nSecond claim.\nKeep this conclusion.")
        for edits in ([ReportEdit(original="absent", replacement="new")],
                      [ReportEdit(original="claim.", replacement="new")],
                      [ReportEdit(original="First claim.", replacement="new"), ReportEdit(original="First", replacement="new")]):
            with self.assertRaises(ValueError):
                apply_repair(draft, ReportRepair(edits=edits))

    def test_repair_requires_a_saved_draft(self):
        with self.assertRaisesRegex(ValueError, "missing draft"):
            resume_report({}, {}, [], None, None, "", "Missing citations")

    def test_uncorrected_citations_still_fail_and_keep_draft_and_reason(self):
        from crewai import Agent
        saved = {}
        sources = {"https://one.test/": {"title": "One", "snippet": "Finding", "retrieved": "2026-10-07"}}
        steps = new_steps()
        for step in steps[:4]:
            step.update(status="completed", output="Finding")
        draft = "No inline links.\n\n## Sources\n"
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}), \
             patch.object(Agent, "execute_task", return_value=ReportRepair(edits=[]).model_dump_json()), \
             patch("src.ai_research_assistant.crew.review_output", side_effect=lambda raw, **kwargs: (True, raw)):
            with self.assertRaisesRegex(ValueError, "guardrail"):
                resume_report({"topic": "Test", "language": "suomi", "current_year": "2026"}, sources,
                              steps, lambda *args: None, lambda **values: saved.update(values), draft, "Missing citations")
        self.assertEqual(saved["draft"], draft)
        self.assertIn("at least two", saved["feedback"])
