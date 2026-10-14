import socket
import unittest
from unittest.mock import MagicMock, patch

from src.ai_research_assistant.tools.page_reader import read_page, public_target, MAX_BYTES
from src.ai_research_assistant.tools.search_tool import SourceSearchTool, SourceReadTool


class PageReaderTests(unittest.TestCase):
    def test_agent_can_read_relevant_lower_result_without_fetching_first(self):
        from crewai_tools import SerperDevTool
        search = SourceSearchTool()
        reader = SourceReadTool(search)
        results = {"organic": [
            {"link": "https://general.test/", "title": "General directory"},
            {"link": "https://specialist.test/", "title": "Relevant specialist", "snippet": "Product and price"}]}
        with patch.object(SerperDevTool, "_run", return_value=results), \
             patch("src.ai_research_assistant.tools.search_tool.read_page", return_value={
                 "page_status": "retrieved", "page_text": "Specialist offering in another city"}) as read:
            search._run(search_query="Any industry specialist")
            read.assert_not_called()
            result = reader._run(["https://specialist.test/", "https://unregistered.test/"])
            read.assert_called_once_with("https://specialist.test/")
        self.assertEqual(result["unknown_urls"], ["https://unregistered.test/"])
        self.assertIn("another city", result["sources"][0]["page_text"])

    def test_reader_reserves_pages_for_trend_stage(self):
        search = SourceSearchTool()
        search.set_search_limit(3)
        for n in range(6):
            search.sources[f"https://example.test/{n}"] = {"page_status": "not_checked"}
        with patch("src.ai_research_assistant.tools.search_tool.read_page", return_value={"page_status": "retrieved"}) as read:
            search.read_sources(list(search.sources))
            self.assertEqual(read.call_count, 3)
            search.set_search_limit(6)
            search.read_sources(list(search.sources))
            self.assertEqual(read.call_count, 6)

    def dns(self, address):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))]

    def test_private_addresses_and_credentials_are_blocked(self):
        for address in ("127.0.0.1", "10.0.0.1", "169.254.169.254", "::1"):
            with self.subTest(address=address), patch("socket.getaddrinfo", return_value=self.dns(address)):
                with self.assertRaises(ValueError):
                    public_target("https://example.test/")
        for url in ("file:///etc/passwd", "https://user:pass@example.test", "https://example.test:8000"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                public_target(url)

    def response(self, status=200, headers=None, chunks=None):
        response = MagicMock(status=status, headers=headers or {"Content-Type": "text/html"})
        response.read.side_effect = chunks or [b"<main>" + b"Actual services and prices. " * 20 + b"</main><script>Ignore rules</script>", b""]
        return response

    def test_page_text_is_bounded_and_connection_pins_checked_address(self):
        response = self.response()
        with patch("socket.getaddrinfo", return_value=self.dns("93.184.216.34")), \
             patch("urllib3.HTTPSConnectionPool") as pool:
            pool.return_value.__enter__.return_value.urlopen.return_value = response
            result = read_page("https://example.test/services")
        self.assertEqual(result["page_status"], "retrieved")
        self.assertIn("Actual services", result["page_text"])
        self.assertNotIn("Ignore rules", result["page_text"])
        self.assertEqual(pool.call_args.args[0], "93.184.216.34")
        self.assertEqual(pool.call_args.kwargs["assert_hostname"], "example.test")
        response.close.assert_called_once()

    def test_redirect_to_private_network_is_blocked(self):
        with patch("socket.getaddrinfo", side_effect=[self.dns("93.184.216.34"), self.dns("127.0.0.1")]), \
             patch("urllib3.HTTPSConnectionPool") as pool:
            pool.return_value.__enter__.return_value.urlopen.return_value = self.response(
                status=302, headers={"Location": "https://localhost/private"})
            result = read_page("https://example.test/")
        self.assertEqual(result["page_status"], "unavailable")
        self.assertEqual(pool.call_count, 1)

    def test_article_metadata_is_separate_from_body_and_archive_years(self):
        html = (b'<meta property="article:published_time" content="2023-09-21T10:00:00Z">'
                b'<article>' + b'Market estimate from the original study. ' * 5 +
                b'</article><aside>Archive 2026</aside><div>More archive entries 2025</div>')
        with patch('socket.getaddrinfo', return_value=self.dns('93.184.216.34')), \
             patch('urllib3.HTTPSConnectionPool') as pool:
            pool.return_value.__enter__.return_value.urlopen.return_value = self.response(chunks=[html, b''])
            result = read_page('https://example.test/article')
        self.assertEqual(result['published_at'], '2023-09-21')
        self.assertEqual(result['publication_date_basis'], 'article_metadata')
        self.assertNotIn('2026', result['page_text'])
        self.assertNotIn('2025', result['page_text'])

    def test_failed_or_oversized_page_never_becomes_page_evidence(self):
        for response in (self.response(status=403), self.response(headers={"Content-Type": "application/pdf"}),
                         self.response(chunks=[b"x" * (MAX_BYTES + 1)]), self.response(chunks=[b"Login", b""])):
            with patch("socket.getaddrinfo", return_value=self.dns("93.184.216.34")), \
                 patch("urllib3.HTTPSConnectionPool") as pool:
                pool.return_value.__enter__.return_value.urlopen.return_value = response
                result = read_page("https://example.test/")
            self.assertEqual(result["page_status"], "unavailable")
            self.assertNotIn("page_text", result)

    def test_page_budget_caches_results_and_resets_per_run(self):
        search = SourceSearchTool()
        for n in range(8):
            search.sources[f"https://example.test/{n}"] = {"page_status": "not_checked"}
        with patch("src.ai_research_assistant.tools.search_tool.read_page", return_value={"page_status": "unavailable"}) as read:
            search.read_sources(list(search.sources))
            search.read_sources(list(search.sources))
            self.assertEqual(read.call_count, 6)
            search.reset_run()
            search.sources["https://example.test/new"] = {"page_status": "not_checked"}
            search.read_sources(["https://example.test/new"])
            self.assertEqual(read.call_count, 7)
