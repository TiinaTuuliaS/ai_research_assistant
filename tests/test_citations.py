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

    def test_evidence_notes_are_required_and_preserved(self):
        valid, incomplete = validate_citations(self.report, self.sources, require_evidence_notes=True)
        self.assertTrue(valid)
        self.assertIn("arvio puuttuu", incomplete)
        self.assertIn("Päätelmien vahvuutta ei ole vahvistettu", incomplete)
        annotated = self.report.replace("## Katsaus", "## Näytön vahvuus ja puutteet")
        note = " — Valmistajan tuotekuvaus tukee ominaisuusvertailua mutta ei osoita kohderyhmän kysyntää tai maksuhalukkuutta."
        annotated = annotated.replace("- [One](https://one.test/report)", "- [One](https://one.test/report)" + note)
        annotated = annotated.replace("- [Two](https://two.test/data)", "- [Two](https://two.test/data)" + note)
        valid, result = validate_citations(annotated, self.sources, require_evidence_notes=True)
        self.assertTrue(valid)
        self.assertIn(note.strip(" —"), result)
        self.assertIn("Suppea lähdepohja", result)

    def test_requires_inline_sources_and_bibliography(self):
        self.assertFalse(validate_citations("## Lähteet\n" + self.report.split("## Lähteet")[1], self.sources)[0])
        self.assertFalse(validate_citations(self.report.split("## Lähteet")[0], self.sources)[0])
        self.assertFalse(validate_citations(self.report, {})[0])
        self.assertFalse(validate_citations(self.report + " https://invented.test", self.sources)[0])

    def test_multiline_notes_and_short_notes_do_not_fail_report(self):
        raw = self.report.replace("- [One](https://one.test/report)", "- [One](https://one.test/report)\n  Tuotekuvaus, ei kysyntänäyttöä.")
        valid, result = validate_citations(raw, self.sources, require_evidence_notes=True)
        self.assertTrue(valid)
        self.assertIn("Tuotekuvaus, ei kysyntänäyttöä.", result)

    def test_missing_bibliography_entry_is_rebuilt_only_from_known_sources(self):
        raw = self.report.replace("- [Two](https://two.test/data)", "")
        self.assertTrue(validate_citations(raw, self.sources)[0])
        self.assertFalse(validate_citations(raw.replace("two.test", "fabricated.test"), self.sources)[0])

    def test_failure_reason_is_logged_without_report_text(self):
        with self.assertLogs("src.ai_research_assistant.citations", level="WARNING") as logs:
            validate_citations("private report body", self.sources)
        self.assertIn("Add a final section", logs.output[0])
        self.assertNotIn("private report body", logs.output[0])

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
