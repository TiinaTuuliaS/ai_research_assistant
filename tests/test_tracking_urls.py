import unittest
from unittest.mock import Mock
from src.ai_research_assistant.source_registry import resolve_source, render_references
from src.ai_research_assistant.quality import review_output


class TrackingURLTests(unittest.TestCase):
    def test_sammakka_url_resolves_and_renders_bare_and_markdown_citations(self):
        base = "https://keepthemspinning.com/blogs/record-store-profiles/record-store-sammakka-pop-ky-tampere"
        registered = base + "?srsltid=original"
        sources = {registered: {"title": "Sammakka", "retrieved": "2026-10-23"}}
        for url in (base, base + "?srsltid=changed"):
            self.assertEqual(resolve_source(url, sources), registered)
            for draft in ("Havainto " + url + ".", f"Havainto [Sammakka]({url})."):
                rendered = render_references(draft, sources)
                self.assertIn("](" + registered + ")", rendered)
                self.assertEqual(render_references(rendered, sources), rendered)
                reviewer = Mock()
                reviewer.call.return_value = {"issues": []}
                valid, result = review_output(draft, sources=sources, brief={}, previous=[], reviewer=reviewer)
                self.assertTrue(valid, result)

    def test_content_parameters_paths_and_fragments_are_not_ignored(self):
        sources = {"https://example.test/item?id=1&srsltid=abc": {}}
        self.assertEqual(resolve_source("https://example.test/item?id=1", sources), next(iter(sources)))
        for url in ("https://example.test/item?id=2", "https://example.test/item", "https://example.test/other?id=1", "https://example.test/item?id=1#other"):
            self.assertIsNone(resolve_source(url, sources))

    def test_ambiguous_tracking_alias_is_not_guessed(self):
        sources = {"https://example.test/?srsltid=a": {}, "https://example.test/?srsltid=b": {}}
        self.assertIsNone(resolve_source("https://example.test/", sources))
        with self.assertRaisesRegex(ValueError, "Unregistered source URL"):
            render_references("Havainto https://example.test/", sources)
        self.assertEqual(resolve_source("https://example.test/?srsltid=a", sources), "https://example.test/?srsltid=a")

    def test_unknown_id_still_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown source IDs"):
            render_references("Havainto [S999]", {"https://example.test/": {}})
