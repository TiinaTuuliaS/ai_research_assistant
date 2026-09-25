import unittest
from unittest.mock import patch

from src.ai_research_assistant.citations import validate_citations
from src.ai_research_assistant.tools.search_tool import SourceSearchTool


class CitationTests(unittest.TestCase):
    def setUp(self):
        self.sources = {
            url: {"title": title, "retrieved": "2026-09-25"}
            for url, title in [("https://one.test/report", "One"), ("https://two.test/data", "Two")]
        }
        self.report = (
            "## Katsaus\nTieto [One](https://one.test/report). "
            "Tieto [Two](https://two.test/data).\n\n## Lähteet\n"
            "- [One](https://one.test/report)\n- [Two](https://two.test/data)"
        )

    def test_valid_report_retains_links_and_adds_evidence_limit(self):
        valid, report = validate_citations(self.report, self.sources)
        self.assertTrue(valid)
        self.assertIn("Haettu 2026-09-25", report)
        self.assertIn("hakutuloskatkelmiin", report)

    def test_rejects_fabricated_sources(self):
        self.assertFalse(validate_citations(self.report.replace("two.test", "invented.test"), self.sources)[0])

    def test_requires_inline_sources_and_bibliography(self):
        self.assertFalse(validate_citations("## Lähteet\n" + self.report.split("## Lähteet")[1], self.sources)[0])
        self.assertFalse(validate_citations(self.report.split("## Lähteet")[0], self.sources)[0])
        self.assertFalse(validate_citations(self.report, {})[0])
        self.assertFalse(validate_citations(self.report + " https://invented.test", self.sources)[0])

    def test_search_collects_real_results_and_isolates_runs(self):
        first = SourceSearchTool()
        second = SourceSearchTool()
        result = {"organic": [{"title": "Report", "link": "https://one.test/a(b)", "snippet": "Evidence"}]}
        with patch.object(SourceSearchTool, "_make_api_request", return_value=result):
            output = first._run(search_query="market")
        self.assertIn("https://one.test/a%28b%29", first.sources)
        self.assertEqual(output["citation_sources"][0]["snippet"], "Evidence")
        self.assertEqual(second.sources, {})


if __name__ == "__main__":
    unittest.main()
