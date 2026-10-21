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
        self.assertIn("hakutuloskatkelmia", report)
        self.assertIn("Kartoitus ei ole kattava", report)

    def test_one_source_is_enough_for_a_narrow_report_but_no_citations_is_rejected(self):
        valid, report = validate_citations("Havainto [One](https://one.test/report).\n\n## Lähteet\n", self.sources)
        self.assertTrue(valid)
        self.assertNotIn("Suppea lähdepohja", report)
        self.assertFalse(validate_citations("Ei viitteitä.\n\n## Lähteet\n", self.sources)[0])

    def test_rejects_fabricated_sources(self):
        self.assertFalse(validate_citations(self.report.replace("two.test", "invented.test"), self.sources)[0])

    def test_discovery_assumption_is_not_published_over_reviewed_source_notes(self):
        self.sources["https://one.test/report"].update(
            selections=[{"reason": "Proves a local market gap"}],
            research_findings=[{"summary": "One foreign example"}])
        raw = self.report.replace("- [One](https://one.test/report)",
                                 "- [One](https://one.test/report) — Foreign example, not local demand.")
        valid, report = validate_citations(raw, self.sources)
        self.assertTrue(valid)
        self.assertIn("Foreign example, not local demand.", report)
        self.assertNotIn("Proves a local market gap", report)

    def test_evidence_section_accepts_other_markdown_heading_levels(self):
        for level in ("#", "###"):
            report = self.report.replace("## Katsaus", level + " Näytön vahvuus ja puutteet")
            valid, result = validate_citations(report, self.sources, require_evidence_notes=True)
            self.assertTrue(valid)
            self.assertNotIn("Raportista puuttuu erillinen", result)

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
        self.assertNotIn("Suppea lähdepohja", result)

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

    def test_bibliography_does_not_count_a_source_removed_from_report_body(self):
        self.sources["https://unused.test/"] = {"title": "Unused", "retrieved": "2026-10-18"}
        raw = self.report + "\n- [Unused](https://unused.test/)"
        valid, report = validate_citations(raw, self.sources)
        self.assertTrue(valid)
        self.assertNotIn("https://unused.test/", report)

    def test_failure_reason_is_logged_without_report_text(self):
        with self.assertLogs("src.ai_research_assistant.citations", level="WARNING") as logs:
            validate_citations("private report body", self.sources)
        self.assertIn("Add a final section", logs.output[0])
        self.assertNotIn("private report body", logs.output[0])

    def test_search_collects_real_results_and_isolates_runs(self):
        first = SourceSearchTool()
        second = SourceSearchTool()
        result = {"organic": [{"title": "Report", "link": "https://one.test/a(b)", "snippet": "Evidence"}]}
        with patch.object(SourceSearchTool, "_make_api_request", return_value=result), \
             patch("src.ai_research_assistant.tools.search_tool.read_page", return_value={"page_status": "unavailable"}):
            output = first._run(search_query="market")
        self.assertIn("https://one.test/a%28b%29", first.sources)
        self.assertEqual(output["citation_sources"][0]["snippet"], "Evidence")
        self.assertEqual(second.sources, {})

    def test_citations_distinguish_page_text_from_snippets(self):
        self.sources["https://one.test/report"].update(page_status="retrieved", page_text="Source text")
        valid, report = validate_citations(self.report, self.sources)
        self.assertTrue(valid)
        self.assertIn("Sivulta poimittu rajattu teksti", report)
        self.assertIn("Vain hakutuloskatkelma", report)


if __name__ == "__main__":
    unittest.main()
