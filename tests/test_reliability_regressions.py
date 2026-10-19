"""Failures reproduced from the October three-mode evaluation."""
import os
import unittest
from unittest.mock import Mock, patch

from src.ai_research_assistant.research_result import ResearchFinding, ResearchResult
from src.ai_research_assistant.evidence import assess_findings
from src.ai_research_assistant.source_registry import unsupported_years
from tests.test_analysis_result import analysis_fixture


def finding(**changes):
    values = dict(title="Palvelu", summary="Yritys tarjoaa huoltoa.", source="S1",
                  supporting_text="Yritys tarjoaa huoltoa.", relevance=8,
                  evidence_kind="offering", entity="Yritys", area=None, period=None,
                  limitations=["Kysyntää ei mitattu."])
    return ResearchFinding(**{**values, **changes})


class ReliabilityRegressions(unittest.TestCase):
    def test_recovered_source_can_keep_offering_after_unsupported_year_is_removed(self):
        from src.ai_research_assistant.evidence import recover_unused_sources, SourceExtraction
        sources = {"https://one.test/": {"source_id": "S1", "snippet": "Yritys tarjoaa huoltoa.",
                                          "selections": [{"reason": "Relevant"}]}}
        assessment = {"assessments": [dict(finding_id="F1", supported=True, scope_supported=True,
                                            single_source_supported=True, reason="Offering") ]}
        reviewer = Mock()
        reviewer.call.side_effect = [
            SourceExtraction(**finding(summary="Yritys tarjoaa huoltoa vuonna 2023.").model_dump(),
                             relevant=True, passage_id=0),
            assessment,
            ResearchResult(topic="Huolto", findings=[finding()]),
            assessment,
        ]
        result = recover_unused_sources(ResearchResult(topic="Huolto", findings=[]), sources, {}, reviewer)
        self.assertEqual(len(result.findings), 1)
        self.assertNotIn("2023", result.findings[0].summary)
        self.assertEqual(result.findings[0].source, "https://one.test/")
        self.assertEqual(reviewer.call.call_count, 4)

    def test_short_menu_passage_keeps_publisher_and_product_context(self):
        from src.ai_research_assistant.evidence import source_passages
        text = "Cafe menu. Bagels. Tuna bagel."
        self.assertEqual(source_passages(text), [text])

    def test_selected_unused_source_is_extracted_without_new_search(self):
        from src.ai_research_assistant.evidence import recover_unused_sources, SourceExtraction
        sources = {"https://one.test/": {"source_id": "S1", "snippet": "Yritys tarjoaa huoltoa.",
                    "selections": [{"reason": "Relevant local offering"}]},
                   "https://unselected.test/": {"snippet": "Unselected search hit"}}
        reviewer = Mock()
        reviewer.call.side_effect = [SourceExtraction(**finding().model_dump(), relevant=True, passage_id=0),
            {"assessments": [dict(finding_id="F1", supported=True, scope_supported=True,
                                  single_source_supported=True, reason="Offering only")]}]
        result = recover_unused_sources(ResearchResult(topic="Huolto", findings=[]), sources, {}, reviewer)
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].source, "https://one.test/")
        self.assertEqual(reviewer.call.call_count, 2)
        self.assertNotIn("Unselected search hit", str(reviewer.call.call_args_list[0]))
        import json
        payload = json.loads(reviewer.call.call_args_list[0].args[0][1]["content"])
        self.assertEqual(payload["url"], "https://one.test/")
        # Already represented sources do not cause another extraction.
        recover_unused_sources(result, sources, {}, reviewer)
        self.assertEqual(reviewer.call.call_count, 2)

    def test_unused_source_recovery_rejects_unknown_passage_index(self):
        from src.ai_research_assistant.evidence import recover_unused_sources, SourceExtraction
        sources = {"https://one.test/": {"snippet": "Yritys tarjoaa huoltoa.", "selections": [{}]}}
        reviewer = Mock()
        reviewer.call.return_value = SourceExtraction(**finding().model_dump(), relevant=True, passage_id=999)
        result = recover_unused_sources(ResearchResult(topic="Huolto", findings=[]), sources, {}, reviewer)
        self.assertEqual(result.findings, [])
        self.assertEqual(reviewer.call.call_count, 1)

    def test_missing_period_support_does_not_discard_valid_observation(self):
        from crewai import Agent
        from src.ai_research_assistant.crew import AiResearchAssistant
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}), \
             patch("src.ai_research_assistant.crew.assess_findings", side_effect=lambda result, *args: (result, [])):
            assistant = AiResearchAssistant()
            assistant.search_tool.sources.update({
                "https://one.test/": {"snippet": "Yritys tarjoaa huoltoa."},
                "https://two.test/": {"snippet": "Yritys tarjoaa huoltoa."}})
            assistant.reviewer = Mock()
            assistant.reviewer.call.side_effect = RuntimeError("Optional repair unavailable")
            task = assistant.research_task()
            result = ResearchResult(topic="Huolto", findings=[finding(),
                finding(title="Perusteeton ajankohta", source="S2", period="2026")])
            with patch.object(Agent, "execute_task", return_value=result) as execute:
                output = task.execute_sync()
            self.assertEqual(execute.call_count, 1)
            self.assertEqual(len(output.pydantic.findings), 1)
            self.assertNotIn("Perusteeton ajankohta", output.raw)
            self.assertIn("Yritys tarjoaa huoltoa", output.raw)
            self.assertEqual(assistant.reviewer.call.call_count, 2)  # Passage repair plus one bounded source recovery.

    def test_undated_snapshot_cannot_pass_as_observed_growth(self):
        record = finding(source="https://one.test/", source_id="S1",
                         evidence_excerpt="Yritys tarjoaa huoltoa.", trend_kind="observed_change")
        reviewer = Mock()
        reviewer.call.return_value = {"assessments": [dict(finding_id="F1", supported=True,
            scope_supported=True, single_source_supported=True, reason="Accepted by model") ]}
        result, reasons = assess_findings(ResearchResult(topic="Huolto", findings=[record]),
            {"https://one.test/": {"snippet": "Yritys tarjoaa huoltoa."}}, {}, reviewer, _repair=False)
        self.assertEqual(result.findings, [])
        self.assertIn("ajankohta", reasons[0])

    def test_local_relevance_cannot_extend_a_single_event_to_requested_year_range(self):
        record = finding(source_id="S1", supporting_text="Yritys tarjoaa huoltoa vuonna 2026.",
                         local_relevance="Osoittaa kehitystä vuosina 2023–2026.")
        self.assertEqual(unsupported_years(record), {"2023"})

    def test_analysis_years_are_bound_to_its_own_findings(self):
        result = analysis_fixture(ids=["F1"])
        ledger = [dict(finding_id="F1", supporting_text="Siirtyi vuonna 2026.", period_support="2026"),
                  dict(finding_id="F2", supporting_text="Toinen asia vuonna 2023.")]
        brief = dict(topic="Test", research_type="market")
        result.answer.statement = "Tarjonta kasvoi vuosina 2023–2026."
        with self.assertRaisesRegex(ValueError, "year absent"):
            result.validate_evidence(ledger, brief)
        result.answer.statement = "Liiketoiminta siirtyi vuonna 2026."
        result.gaps = ["Vuosien 2023–2026 kokonaiskehitys ei selviä."]
        result.validate_evidence(ledger, brief)
