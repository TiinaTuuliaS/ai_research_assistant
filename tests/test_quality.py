import unittest
from unittest.mock import Mock, patch

from src.ai_research_assistant.quality import review_output, QualityReview, ReviewIssue, COMPETITION_REVIEW_RULES
from src.ai_research_assistant.tools.search_tool import SourceSearchTool


class QualityTests(unittest.TestCase):
    def test_researcher_cannot_spend_trend_search_reserve(self):
        tool = SourceSearchTool()
        tool.set_search_limit(3)
        with patch("crewai_tools.SerperDevTool._run", return_value={"organic": []}) as search:
            for _ in range(5):
                tool._run(search_query="local evidence")
            self.assertEqual(search.call_count, 3)
            tool.set_search_limit(6)
            for _ in range(5):
                tool._run(search_query="international developments")
            self.assertEqual(search.call_count, 6)

    def test_reviewer_receives_accepted_evidence_and_can_limit_provider_count(self):
        import json
        source = {"url": "https://example.test/services", "snippet": "Indoor cycling",
                  "page_status": "retrieved", "page_text": "Tampereen toimipiste: sisäpyöräily tiistaisin.",
                  "research_findings": [{"summary": "Tampereella järjestetään sisäpyöräilyä.",
                                         "supporting_text": "Tampereen toimipiste: sisäpyöräily tiistaisin."}]}
        reviewer = Mock()
        reviewer.call.return_value = QualityReview(issues=[ReviewIssue(
            excerpt="Tampereella on vain kaksi spinning-salia.",
            correction="Haussa löytyi kaksi esimerkkiä spinningin tarjoajista. Kartoitus ei ole kattava.")])
        ok, result = review_output("Tampereella on vain kaksi spinning-salia.",
                                  sources={source["url"]: source}, brief={"research_type": "market"},
                                  previous=[], reviewer=reviewer)
        self.assertTrue(ok)
        self.assertNotIn("vain kaksi", result)
        self.assertIn("Kartoitus ei ole kattava", result)
        messages = reviewer.call.call_args.args[0]
        payload = json.loads(messages[1]["content"])
        self.assertNotIn("page_text", payload["retrieved_evidence"][0])
        self.assertEqual(payload["original_findings"], source["research_findings"])
        self.assertNotIn("research_findings", payload["retrieved_evidence"][0])
        self.assertNotIn("previous_stages", payload)
        self.assertIn("total-provider counts", messages[0]["content"])

    def test_competition_review_preserves_evidence_when_correcting_recommendation(self):
        import json

        evidence = "Kilpailija tarjoaa vegaanisen buffetin [Menu](https://example.test/menu)."
        claim = "Erotut vegaanisella buffetilla."
        correction = "Vegaaninen buffet vastaisi nykyiseen kilpailuun; eroa ei ole vielä osoitettu."
        sources = {"https://example.test/menu": {"research_findings": [{"summary": "Vegaaninen buffet"}]}}
        reviewer = Mock()
        reviewer.call.return_value = QualityReview(issues=[ReviewIssue(excerpt=claim, correction=correction)])
        ok, result = review_output(evidence + "\n" + claim, sources=sources,
                                  brief={"research_type": "competition"}, previous=[], reviewer=reviewer)
        self.assertTrue(ok)
        self.assertIn(evidence, result)
        self.assertIn(correction, result)
        messages = reviewer.call.call_args.args[0]
        self.assertIn(COMPETITION_REVIEW_RULES, messages[0]["content"])
        self.assertEqual(json.loads(messages[1]["content"])["original_findings"], sources["https://example.test/menu"]["research_findings"])

    def test_competition_rules_are_scoped_and_honest_proposals_can_pass(self):
        reviewer = Mock()
        reviewer.call.return_value = QualityReview(issues=[])
        text = "Testattava ehdotus: iltapalvelu. Kilpailijoiden aukioloajoista ei ole tietoa."
        for mode in ("competition", "market"):
            with self.subTest(mode=mode):
                self.assertEqual(review_output(text, sources={}, brief={"research_type": mode},
                                               previous=[], reviewer=reviewer), (True, text))
                prompt = reviewer.call.call_args.args[0][0]["content"]
                self.assertEqual(COMPETITION_REVIEW_RULES in prompt, mode == "competition")

    def test_reviewer_receives_original_evidence_and_corrects_material_issues(self):
        sources = {"https://example.test/menu": {"url": "https://example.test/menu",
            "research_findings": [{"summary": "Lounas 12 euroa", "evidence_kind": "price"}]}}
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

    def test_user_assumption_is_separate_from_factual_evidence(self):
        import json
        reviewer = Mock()
        reviewer.call.return_value = QualityReview(issues=[])
        review_output("Aineisto on rajallinen.", sources={},
                      brief={"goal": "There are no competitors", "language": "suomi"},
                      previous=[{"text": "There are no competitors"}], reviewer=reviewer)
        payload = json.loads(reviewer.call.call_args.args[0][1]["content"])
        self.assertNotIn("goal", payload["brief"])
        self.assertEqual(payload["unverified_user_context"]["goal"], "There are no competitors")
        self.assertEqual(payload["original_findings"], [])
        self.assertNotIn("previous_stages", payload)

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
