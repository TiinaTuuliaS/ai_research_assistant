import unittest

from src.ai_research_assistant.analysis_result import AnalysisResult, render_analysis


def analysis_fixture(topic="Test", mode="market", ids=None):
    return AnalysisResult(research_type=mode, topic=topic,
        answer=dict(statement="Perusteltu ehdollinen näkemys. Aineisto ei osoita kysyntää.",
                    finding_ids=[] if ids is None else ids, uncertainty="Käyttömäärä ei selviä."),
        conclusions=[], comparisons=[], recommendation="Arvioi rajattua vaihtoehtoa.",
        alternative="Odota vahvempaa näyttöä.", gaps=["Kysyntä ei selviä."])


class AnalysisTests(unittest.TestCase):
    def test_synthesis_model_is_separate_and_can_fall_back_to_research_model(self):
        import os
        from unittest.mock import patch
        from src.ai_research_assistant.crew import AiResearchAssistant
        for model in ("openai/gpt-4.1", ""):
            with self.subTest(model=model), patch.dict(os.environ, {
                "OPENAI_API_KEY": "test", "SERPER_API_KEY": "test",
                "RESEARCH_MODEL": "openai/gpt-4.1-mini", "SYNTHESIS_MODEL": model}):
                assistant = AiResearchAssistant()
                expected = "gpt-4.1" if model else "gpt-4.1-mini"
                self.assertTrue(assistant.analyst().llm.model.endswith(expected))
                self.assertTrue(assistant.writer().llm.model.endswith(expected))
                self.assertTrue(assistant.report_reviewer.model.endswith(expected))
                self.assertTrue(assistant.reviewer.model.endswith("gpt-4.1-mini"))

    def test_filtered_sources_keep_sparse_registry_ids_for_writer(self):
        result = analysis_fixture(ids=["F1", "F2"])
        ledger = [dict(finding_id="F1", source="https://first.test/", source_id="S1"),
                  dict(finding_id="F2", source="https://local.test/", source_id="S21")]
        text = render_analysis(result, ledger)
        self.assertIn("[Lähde S21](https://local.test/)", text)
        self.assertNotIn("[Lähde S2]", text)

    def test_real_three_task_pipeline_for_each_mode(self):
        import os
        from unittest.mock import patch
        from crewai import Agent
        from src.ai_research_assistant.crew import AiResearchAssistant
        from src.ai_research_assistant.research_result import ResearchFinding, ResearchResult
        for mode in ("competition", "market"):
            with self.subTest(mode=mode), patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}), \
                 patch("src.ai_research_assistant.crew.assess_findings", side_effect=lambda result, *args: (result, [])), \
                 patch("src.ai_research_assistant.crew.review_output", side_effect=lambda raw, **kwargs: (True, raw)):
                assistant = AiResearchAssistant()
                calls = []
                def execute(agent, task, context=None, tools=None):
                    calls.append(task.name)
                    if task.name == "research_task":
                        findings = []
                        for i in (1, 2):
                            assistant.search_tool.sources[f"https://source{i}.test/"] = {
                                "snippet": "Offers a service.", "title": "Source", "retrieved": "2026-10-16"}
                            findings.append(ResearchFinding(title="Offering", summary="Offers a service.",
                                source=f"S{i}", supporting_text="Offers a service.", relevance=8,
                                evidence_kind="offering", entity=f"Company {i}", area=None, period=None,
                                limitations=["Demand unknown."]))
                        return ResearchResult(topic="Test", findings=findings)
                    self.assertIn("F1", context)
                    if task.name == "analysis_task":
                        import json
                        # Only the checked ledger crosses the research boundary.
                        payload = json.loads(context)
                        self.assertEqual(len(payload["accepted_findings"]), 2)
                        self.assertEqual(payload["accepted_findings"][0]["supporting_text"], "Offers a service.")
                        return analysis_fixture(mode=mode, ids=["F1", "F2"])
                    self.assertIn("Perusteltu ehdollinen", context)
                    return "Limited offering [S1] [S2].\n\n## Sources\n"
                with patch.object(Agent, "execute_task", execute):
                    result = assistant.crew().kickoff(inputs=dict(topic="Test", language="english",
                                                                  research_type=mode, current_year="2026"))
                self.assertEqual(calls, ["research_task", "analysis_task", "report_task"])
                self.assertIsInstance(result.tasks_output[1].pydantic, AnalysisResult)
                self.assertIn("https://source1.test/", result.raw)

    def test_analysis_guardrail_retries_unknown_ids_once(self):
        import os
        from unittest.mock import patch
        from crewai import Agent
        from src.ai_research_assistant.crew import AiResearchAssistant
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}):
            assistant = AiResearchAssistant()
            assistant.prepare(dict(topic="Test", research_type="market"))
            task = assistant.analysis_task()
            with patch.object(Agent, "execute_task", side_effect=[analysis_fixture(ids=["F999"]),
                                                                 analysis_fixture()]) as execute:
                output = task.execute_sync()
            self.assertEqual(execute.call_count, 2)
            self.assertIsInstance(output.pydantic, AnalysisResult)
            self.assertNotIn("F999", output.raw)

    def test_all_modes_preserve_topic_and_bind_answer_to_evidence(self):
        ledger = [dict(finding_id="F1", source="https://example.test/", entity="Competitor")]
        for mode in ("competition", "market"):
            result = analysis_fixture(mode=mode, ids=["F1"])
            brief = dict(topic="Test", research_type=mode)
            result.validate_evidence(ledger, brief)
            self.assertIn("https://example.test/", render_analysis(result, ledger))
            result.answer.finding_ids = ["F999"]
            with self.assertRaisesRegex(ValueError, "accepted finding"):
                result.validate_evidence(ledger, brief)
            result.answer.finding_ids = []
            with self.assertRaisesRegex(ValueError, "at least one"):
                result.validate_evidence(ledger, brief)
            result.validate_evidence([], brief)
            with self.assertRaisesRegex(ValueError, "topic"):
                result.validate_evidence([], {**brief, "topic": "Competitor"})

    def test_competitor_must_belong_to_referenced_observation(self):
        from src.ai_research_assistant.analysis_result import Comparison
        result = analysis_fixture(mode="competition", ids=["F1"])
        result.comparisons = [Comparison(competitor="Other", feature="Price", status="unknown",
                                         finding_ids=["F1"], limitation="Unknown")]
        ledger = [dict(finding_id="F1", entity="Competitor")]
        brief = dict(topic="Test", research_type="competition")
        with self.assertRaisesRegex(ValueError, "competitor"):
            result.validate_evidence(ledger, brief)
        result.comparisons[0].competitor = "Competitor"
        result.validate_evidence(ledger, brief)

    def test_single_company_feature_is_not_a_comparison(self):
        from src.ai_research_assistant.analysis_result import Comparison
        result = analysis_fixture(mode="competition", ids=["F1"])
        ledger = [dict(finding_id="F1", entity="Competitor")]
        brief = dict(topic="Test", research_type="competition")
        for status in ("shared", "evidenced_difference"):
            result.comparisons = [Comparison(competitor="Competitor", feature="Nouto",
                status=status, finding_ids=["F1"], limitation="Muiden tarjonta ei selviä.")]
            with self.assertRaisesRegex(ValueError, "both compared entities"):
                result.validate_evidence(ledger, brief)
        result.comparisons[0].status = "unknown"
        result.validate_evidence(ledger, brief)
        ledger.append(dict(finding_id="F2", entity="Other"))
        result.comparisons[0].finding_ids.append("F2")
        result.comparisons[0].status = "shared"
        result.validate_evidence(ledger, brief)

    def test_saved_five_step_job_can_still_retry(self):
        from types import SimpleNamespace
        from src.api import retry_available
        for keys in (["researcher", "analyst", "writer"],
                     ["researcher", "trend_analyst", "analyst", "strategist", "writer"]):
            steps = [dict(key=key, status="completed", output="Saved output") for key in keys]
            steps[-1].update(status="failed", output="")
            job = SimpleNamespace(status="failed", steps=steps)
            saved = SimpleNamespace(inputs={"current_year": "2026"}, sources={"source": {}},
                                    draft="Draft", feedback="Repair")
            self.assertTrue(retry_available(job, saved))
            steps[0]["status"] = "failed"
            self.assertFalse(retry_available(job, saved))
