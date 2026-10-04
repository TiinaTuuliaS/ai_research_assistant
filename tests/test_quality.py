import unittest
from unittest.mock import Mock, patch

from src.ai_research_assistant.quality import review_output, QualityReview, ReviewIssue
from src.ai_research_assistant.tools.search_tool import SourceSearchTool


class QualityTests(unittest.TestCase):
    def test_reviewer_receives_original_evidence_and_corrects_material_issues(self):
        sources = {"https://example.test/menu": {"url": "https://example.test/menu", "snippet": "Lounas 12 euroa"}}
        reviewer = Mock()
        reviewer.call.return_value = QualityReview(issues=[ReviewIssue(
            excerpt="Asiakkaat maksavat mielellään 12 euroa.",
            correction="Hinnasto kertoo pyydetyn hinnan, ei toteutuneita ostoja.")])
        ok, feedback = review_output("Asiakkaat maksavat mielellään 12 euroa.", sources=sources,
                                    brief={"language": "suomi"}, previous=[], reviewer=reviewer)
        self.assertTrue(ok)
        self.assertIn("ei toteutuneita ostoja", feedback)
        self.assertIn("Lounas 12 euroa", reviewer.call.call_args.args[0][1]["content"])

    def test_reviewer_cannot_add_unknown_source_links(self):
        reviewer = Mock()
        reviewer.call.return_value = QualityReview(issues=[ReviewIssue(
            excerpt="Väite", correction="[Uusi lähde](https://invented.test/)")])
        self.assertFalse(review_output("Väite", sources={}, brief={}, previous=[], reviewer=reviewer)[0])

    def test_accepts_uncertainty_without_rewriting_text(self):
        reviewer = Mock()
        reviewer.call.return_value = '{"issues": []}'
        text = "Aineisto ei riitä kysynnän arviointiin."
        self.assertEqual(review_output(text, sources={}, brief={}, previous=[], reviewer=reviewer), (True, text))

    def test_invalid_review_does_not_silently_pass(self):
        reviewer = Mock()
        reviewer.call.return_value = "not JSON"
        self.assertFalse(review_output("Teksti", sources={}, brief={}, previous=[], reviewer=reviewer)[0])

    def test_reviewer_noop_or_invented_excerpt_does_not_reject_honest_gap(self):
        reviewer = Mock()
        text = "Kysynnästä ei löytynyt suoraa näyttöä."
        reviewer.call.return_value = QualityReview(issues=[
            ReviewIssue(excerpt=text, correction=text),
            ReviewIssue(excerpt="Kysyntä kasvaa", correction="DELETE"),
        ])
        self.assertEqual(review_output(text, sources={}, brief={}, previous=[], reviewer=reviewer), (True, text))

    def test_unknown_links_rejected_before_paid_review(self):
        reviewer = Mock()
        self.assertFalse(review_output("[Lähde](https://invented.test/)", sources={}, brief={}, previous=[], reviewer=reviewer)[0])
        reviewer.call.assert_not_called()

    def test_search_budget_survives_retries_and_resets_between_runs(self):
        tool = SourceSearchTool()
        with patch("crewai_tools.SerperDevTool._run", return_value={"organic": []}) as search:
            for _ in range(9):
                tool._run(search_query="test")
            self.assertEqual(search.call_count, 6)
            tool.reset_run()
            tool._run(search_query="test")
            self.assertEqual(search.call_count, 7)
