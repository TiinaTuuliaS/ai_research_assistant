import unittest
from src.ai_research_assistant.research_contract import bind_entities, resolve_comparisons
from src.ai_research_assistant.analysis_result import AnalysisResult


def result(rows):
    return AnalysisResult(research_type="competition", topic="Test",
        answer=dict(statement="Havainto.", finding_ids=["F1"], uncertainty="Rajattu."),
        conclusions=[], comparisons=rows, gaps=[])


def row(**changes):
    return dict(competitor_id="E1", feature="Aukiolo", status="unknown", finding_ids=["F1"], limitation="Rajattu.", **changes)


class EntityIdentityTests(unittest.TestCase):
    def test_display_name_comes_from_referenced_finding(self):
        findings = [dict(finding_id="F1", entity="Laukontorin antikvariaatti"),
                    dict(finding_id="F2", entity="Laukontorin Antikvariaatti")]
        bind_entities(findings)
        analysis = result([row()])
        resolve_comparisons(analysis, findings)
        self.assertEqual(analysis.comparisons[0].competitor, findings[0]["entity"])
        analysis.validate_evidence(findings, dict(topic="Test", research_type="competition"))

    def test_case_and_spacing_do_not_create_two_comparison_parties(self):
        findings = [dict(finding_id="F1", entity="Levykauppa Äx"),
                    dict(finding_id="F2", entity="  LEVYKAUPPA   ÄX ")]
        bind_entities(findings)
        self.assertEqual(findings[0]["entity_id"], findings[1]["entity_id"])
        analysis = result([dict(row(), competitor="Levykauppa Äx", status="shared", finding_ids=["F1", "F2"])])
        with self.assertRaisesRegex(ValueError, "both compared entities"):
            analysis.validate_evidence(findings, dict(topic="Test", research_type="competition"))
        resolve_comparisons(analysis, findings)
        self.assertEqual(analysis.comparisons, [])

    def test_misspelled_unidentified_row_is_removed_without_losing_valid_analysis(self):
        findings = [dict(finding_id="F1", entity="Levykauppa Äx")]
        bind_entities(findings)
        analysis = result([row(), dict(row(), competitor_id="", competitor="Levykaupa Äx")])
        resolve_comparisons(analysis, findings)
        self.assertEqual(len(analysis.comparisons), 1)
        self.assertTrue(analysis.gaps)
        analysis.validate_evidence(findings, dict(topic="Test", research_type="competition"))

    def test_unsupported_company_id_does_not_borrow_another_company_evidence(self):
        findings = [dict(finding_id="F1", entity="Äx"), dict(finding_id="F2", entity="Swamp")]
        bind_entities(findings)
        analysis = result([dict(row(), competitor_id="E2")])
        resolve_comparisons(analysis, findings)
        self.assertEqual(analysis.comparisons, [])
