import json
import os
import unittest
from unittest.mock import Mock, patch

from pydantic import ValidationError

from src.ai_research_assistant.evidence import assess_findings, check_excerpts, evidence_ledger
from src.ai_research_assistant.quality import QualityReview, ReviewIssue, review_output
from src.ai_research_assistant.research_result import ResearchFinding, ResearchOutputError, ResearchResult


class EvidenceTests(unittest.TestCase):
    def test_scope_failure_overrides_general_support_and_is_recorded(self):
        reviewer = Mock()
        reviewer.call.return_value = {"assessments": [{"finding_id": "F1", "supported": True,
            "scope_supported": False, "single_source_supported": True,
            "reason": "Yksi toimija ei osoita koko alueen tarjontaa."}]}
        sources = self.sources()
        sources["https://other.test/"] = {"snippet": "UNRELATED SOURCE"}
        result, excluded = assess_findings(self.result(), sources, {}, reviewer)
        self.assertEqual(result.findings, [])
        self.assertEqual(len(excluded), 1)
        self.assertNotIn("UNRELATED SOURCE", reviewer.call.call_args.args[0][1]["content"])
        self.assertFalse(sources["https://example.test/services"]["finding_reviews"][0]["scope_supported"])

    def test_malformed_review_is_retried_without_repeating_research(self):
        reviewer = Mock()
        reviewer.call.side_effect = ["invalid JSON", {"assessments": [
            {"finding_id": "F1", "supported": True, "scope_supported": True, "single_source_supported": True, "reason": "Lähde tukee tarjontaa."}]}]
        result, excluded = assess_findings(self.result(), self.sources(), {}, reviewer)
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(excluded, [])
        self.assertEqual(reviewer.call.call_count, 2)

    def test_invalid_review_has_a_bounded_retry_count(self):
        reviewer = Mock()
        reviewer.call.return_value = {"assessments": []}
        with self.assertRaises(ResearchOutputError):
            assess_findings(self.result(), self.sources(), {}, reviewer)
        self.assertEqual(reviewer.call.call_count, 2)

    def test_provider_validation_failure_can_recover(self):
        from src.ai_research_assistant.evidence import EvidenceReview
        try:
            EvidenceReview.model_validate({"assessments": [{"supported": "bad"}]})
        except ValidationError as exc:
            failure = exc
        reviewer = Mock()
        reviewer.call.side_effect = [failure, {"assessments": [
            {"finding_id": "F1", "supported": True, "scope_supported": True, "single_source_supported": True, "reason": "Lähde tukee tarjontaa."}]}]
        result, _ = assess_findings(self.result(), self.sources(), {}, reviewer)
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(reviewer.call.call_count, 2)

    def test_crewai_wire_schema_preserves_unknown_scope(self):
        from crewai.utilities.pydantic_schema_utils import generate_model_description
        schema = generate_model_description(ResearchResult)["json_schema"]["schema"]
        fields = schema["properties"]["findings"]["items"]["properties"]
        for name in ("entity", "area", "period"):
            self.assertEqual(fields[name]["type"], "string")
            self.assertNotIn("minLength", fields[name])
        self.assertIsNone(self.finding(entity=None, area=None, period=None).period)
        self.assertIsNone(self.finding(period=" ").period)
        with self.assertRaises(ValidationError):
            self.finding(period=123)

    def test_null_snippet_does_not_hide_valid_page_evidence(self):
        sources = self.sources()
        sources["https://example.test/services"]["snippet"] = None
        check_excerpts(self.result(), sources)
        with self.assertRaises(ResearchOutputError):
            check_excerpts(self.result(evidence_excerpt=""), sources)

    def finding(self, **changes):
        values = dict(title="Ohjattu tunti", summary="Well Gym ilmoittaa tarjoavansa spinning-tunteja.",
                      source="https://example.test/services", relevance=9,
                      evidence_excerpt="Spin-tunnit alkavat Tampereella 3.1.2025.",
                      evidence_kind="offering", entity="Well Gym", area="Tampere", period="3.1.2025",
                      limitations=["Osallistujamäärä ja maksuhalukkuus eivät selviä."])
        return ResearchFinding(**{**values, **changes})

    def sources(self):
        return {"https://example.test/services": {"page_status": "retrieved",
                "page_text": "Spin-tunnit alkavat Tampereella 3.1.2025.", "snippet": "Spin-tunnit"}}

    def result(self, **changes):
        return ResearchResult(topic="Spinning Tampereella", findings=[self.finding(**changes)])

    def test_required_evidence_fields_and_taxonomy(self):
        for key in ("evidence_kind", "entity", "area", "period", "limitations"):
            values = self.finding().model_dump()
            del values[key]
            with self.subTest(key=key), self.assertRaises(ValidationError):
                ResearchFinding.model_validate(values)
        for changes in ({"evidence_kind": "verified_demand"}, {"limitations": []}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                self.finding(**changes)

    def test_excerpt_must_exist_in_own_source_not_another_page(self):
        sources = self.sources()
        sources["https://other.test/"] = {"snippet": "300 maksavaa asiakasta"}
        with self.assertRaisesRegex(ResearchOutputError, "lähdekatkelmaa"):
            check_excerpts(self.result(evidence_excerpt="300 maksavaa asiakasta"), sources)
        check_excerpts(self.result(evidence_excerpt="Spin-tunnit\n alkavat Tampereella 3.1.2025."), sources)
        sources["https://example.test/services"]["page_status"] = "unavailable"
        with self.assertRaises(ResearchOutputError):
            check_excerpts(self.result(), sources)

    def test_demand_report_offering_is_not_accepted_as_demand(self):
        reviewer = Mock()
        reviewer.call.return_value = {"assessments": [{"finding_id": "F1", "supported": False,
            "scope_supported": True, "single_source_supported": False,
            "reason": "Tarjonta ei osoita toteutunutta kysyntää."}]}
        result, excluded = assess_findings(self.result(summary="Tämä on suoraa näyttöä kysynnästä.",
            evidence_kind="usage"), self.sources(), {"research_type": "market", "language": "suomi"}, reviewer)
        self.assertEqual(result.findings, [])
        self.assertIn("Tarjonta ei osoita", excluded[0])
        request = json.loads(reviewer.call.call_args.args[0][1]["content"])
        self.assertEqual(request["findings"][0]["evidence_kind"], "usage")
        self.assertEqual(request["findings"][0]["own_evidence"], self.sources()["https://example.test/services"])
        self.assertNotIn("sources", request)

    def test_incomplete_or_duplicate_assessment_cannot_pass(self):
        reviewer = Mock()
        item = {"finding_id": "F1", "supported": True, "scope_supported": True, "single_source_supported": True, "reason": "Tarjonta."}
        for response in ("bad JSON", {"assessments": []}, {"assessments": [item, item]},
                         {"assessments": [{**item, "finding_id": "F2"}]}):
            reviewer.call.return_value = response
            with self.subTest(response=response), self.assertRaises(ResearchOutputError):
                assess_findings(self.result(), self.sources(), {}, reviewer)

    def test_accepted_evidence_is_checkpointed_and_rejected_claim_is_not_forwarded(self):
        from crewai.tasks.task_output import TaskOutput
        from src.ai_research_assistant.crew import AiResearchAssistant
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "SERPER_API_KEY": "test"}):
            assistant = AiResearchAssistant()
            assistant.search_tool.sources.update(self.sources())
            assistant.reviewer = Mock()
            assistant.checkpoint = Mock()
            assistant.reviewer.call.return_value = {"assessments": [
                {"finding_id": "F1", "supported": True, "scope_supported": True, "single_source_supported": True, "reason": "Tarjonta."},
                {"finding_id": "F2", "supported": False, "scope_supported": False, "single_source_supported": False, "reason": "Ainutlaatuisuudesta ei ole näyttöä."}]}
            result = ResearchResult(topic="Spinning", findings=[self.finding(),
                self.finding(title="Tampereella ei ole muita saleja")])
            output = TaskOutput(description="Test", agent="Tutkija", raw="", pydantic=result)
            assistant.accept_research(output)
            self.assertNotIn("ei ole muita saleja", output.raw)
            self.assertNotIn("Ainutlaatuisuudesta ei ole näyttöä", output.raw)
            self.assertIn("Ainutlaatuisuudesta ei ole näyttöä.", assistant.excluded_findings)
            self.assertEqual(len(output.pydantic.findings), 1)
            saved = assistant.checkpoint.call_args.kwargs["sources"]
            ledger = evidence_ledger(json.loads(json.dumps(saved)))
            self.assertEqual(ledger[0]["finding_id"], "F1")
            self.assertEqual(ledger[0]["evidence_kind"], "offering")
            self.assertEqual(ledger[0]["limitations"], self.finding().limitations)

    def test_final_report_rechecks_corrected_competition_conclusion(self):
        sources = self.sources()
        sources["https://example.test/services"]["research_findings"] = [
            {"finding_id": "F1", **self.finding().model_dump(mode="json")}]
        reviewer = Mock()
        raw = "Erotut virtuaalitunneilla, joita GOGO jo tarjoaa."
        corrected = "Virtuaalitunnit vastaisivat nykyiseen kilpailuun; eroa GOGOon ei ole osoitettu."
        reviewer.call.side_effect = [QualityReview(issues=[ReviewIssue(excerpt=raw, correction=corrected)]),
                                     QualityReview(issues=[])]
        ok, text = review_output(raw, sources=sources, brief={"research_type": "competition"},
                                 previous=[{"text": raw}], reviewer=reviewer, final_report=True)
        self.assertTrue(ok)
        self.assertEqual(text, corrected)
        self.assertEqual(reviewer.call.call_count, 2)
        for call in reviewer.call.call_args_list:
            data = json.loads(call.args[0][1]["content"])
            self.assertEqual(data["original_findings"][0]["finding_id"], "F1")
        self.assertEqual(json.loads(reviewer.call.call_args.args[0][1]["content"])["draft"], corrected)

    def test_second_pass_correction_is_preserved_without_another_rewrite(self):
        reviewer = Mock()
        reviewer.call.side_effect = [
            QualityReview(issues=[ReviewIssue(excerpt="A", correction="B")]),
            QualityReview(issues=[ReviewIssue(excerpt="B", correction="C")]),
        ]
        ok, feedback = review_output("A", sources={}, brief={"research_type": "market"}, previous=[],
                                     reviewer=reviewer, final_report=True)
        self.assertTrue(ok)
        self.assertEqual(feedback, "C")
        self.assertEqual(reviewer.call.call_count, 2)

    def test_empty_evidence_is_honest_and_uses_no_assessment_call(self):
        reviewer = Mock()
        result = ResearchResult(topic="Test", findings=[])
        self.assertEqual(assess_findings(result, {}, {}, reviewer), (result, []))
        reviewer.call.assert_not_called()

    def test_new_search_keeps_original_findings_for_report_repair(self):
        from src.ai_research_assistant.tools.search_tool import SourceSearchTool
        tool = SourceSearchTool()
        tool.sources.update(self.sources())
        findings = [{"finding_id": "F1", **self.finding().model_dump(mode="json")}]
        tool.sources["https://example.test/services"]["research_findings"] = findings
        with patch("crewai_tools.SerperDevTool._run", return_value={"organic": [
            {"link": "https://example.test/services", "title": "Palvelut", "snippet": "New snippet"}]}):
            tool._run(search_query="same source")
        self.assertEqual(evidence_ledger(tool.sources), findings)

    def test_review_contract_is_shared_by_all_modes(self):
        reviewer = Mock()
        reviewer.call.return_value = QualityReview(issues=[])
        sources = self.sources()
        sources["https://example.test/services"]["research_findings"] = [
            {"finding_id": "F1", **self.finding().model_dump(mode="json")}]
        for mode in ("competition", "market"):
            with self.subTest(mode=mode):
                ok, _ = review_output("Aineisto ei riitä johtopäätökseen.", sources=sources,
                    brief={"research_type": mode}, previous=[], reviewer=reviewer, final_report=True)
                self.assertTrue(ok)
                messages = reviewer.call.call_args.args[0]
                self.assertIn("opening answer", messages[0]["content"])
                self.assertEqual(json.loads(messages[1]["content"])["original_findings"][0]["evidence_kind"], "offering")
