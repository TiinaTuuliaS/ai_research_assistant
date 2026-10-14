import json
import os
import unittest
from unittest.mock import Mock, patch

from crewai_tools import SerperDevTool
from src.ai_research_assistant.source_registry import register_sources, render_references, resolve_source
from src.ai_research_assistant.research_result import ResearchFinding, ResearchResult, render_research
from src.ai_research_assistant.evidence import filter_excerpt_findings, assess_findings, finding_record
from src.ai_research_assistant.citations import validate_citations
from src.ai_research_assistant.quality import review_output, QualityReview
from src.ai_research_assistant.tools.search_tool import SourceSearchTool, SourceReadTool


class SourceRegistryTests(unittest.TestCase):
    def sources(self):
        return {'https://example.test/2023/09/21/report/': {
            'title': 'Market report', 'retrieved': '2026-10-14', 'page_status': 'retrieved',
            'page_text': 'The market was 895 million euros in 2023. Archive 2026',
            'snippet': 'A market report.'}}

    def finding(self, **changes):
        return ResearchFinding(**{**dict(title='Markkinan koko', summary='Markkinan arvoksi arvioitiin 895 miljoonaa euroa vuonna 2023.',
            source='S1', supporting_text='The market was 895 million euros in 2023.',
            period_support='895 million euros in 2023', relevance=9, evidence_kind='other',
            entity=None, area=None, period='2023', limitations=['Ei erittele huonekaluja.']), **changes})

    def test_ids_are_stable_across_searches_and_checkpoint_restore(self):
        tool = SourceSearchTool()
        result = {'organic': [{'link': 'https://one.test/', 'title': 'One'}]}
        with patch.object(SerperDevTool, '_run', return_value=result):
            tool._run(search_query='one')
            tool._run(search_query='again')
        self.assertEqual(tool.sources['https://one.test/']['source_id'], 'S1')
        saved = json.loads(json.dumps(tool.sources))
        saved['https://two.test/'] = {}
        register_sources(saved)
        self.assertEqual(saved['https://one.test/']['source_id'], 'S1')
        self.assertEqual(resolve_source('S2', saved), 'https://two.test/')
        self.assertIsNone(resolve_source('S999', saved))
        reader = SourceReadTool(tool)
        with patch('src.ai_research_assistant.tools.search_tool.read_page', return_value={'page_status': 'unavailable'}):
            self.assertEqual(reader._run(['S1'])['sources'][0]['url'], 'https://one.test/')

    def test_publication_retrieval_and_observation_dates_are_distinct(self):
        sources = self.sources()
        sources['https://unknown.test/'] = {'title': 'Unknown', 'retrieved': '2026-10-14', 'published': 'today'}
        register_sources(sources)
        original = next(iter(sources.values()))
        self.assertEqual(original['published_at'], '2023-09-21')
        self.assertEqual(original['retrieved_at'], '2026-10-14')
        self.assertIsNone(sources['https://unknown.test/']['published_at'])
        valid, text = validate_citations('Havainto [S1]. Toinen [S2].\n\n## Lähteet\n', sources)
        self.assertTrue(valid)
        self.assertIn('Julkaistu 2023-09-21', text)
        self.assertIn('Haettu 2026-10-14', text)
        self.assertIn('Julkaisupäivä ei tiedossa', text)
        self.assertNotIn('[S1]', text)

    def test_unknown_id_fails_before_model_call_and_links_are_exact(self):
        sources = self.sources()
        text = render_references('Havainto [S1].', sources)
        self.assertIn('](https://example.test/2023/09/21/report/)', text)
        self.assertEqual(render_references(text, sources), text)
        reviewer = Mock()
        valid, _ = review_output('Havainto [S2]', sources=sources, brief={}, previous=[], reviewer=reviewer)
        self.assertFalse(valid)
        reviewer.call.assert_not_called()
        valid, _ = review_output('Lähde: https://exampel.test/report', sources=sources, brief={}, previous=[], reviewer=reviewer)
        self.assertFalse(valid)
        reviewer.call.assert_not_called()

    def test_support_must_belong_to_the_selected_source_and_remains_private(self):
        sources = self.sources()
        sources['https://other.test/'] = {'snippet': 'A different business has 500 customers.'}
        findings = [self.finding(), self.finding(supporting_text='A different business has 500 customers.')]
        result, excluded = filter_excerpt_findings(ResearchResult(topic='Test', findings=findings), sources)
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(len(excluded), 1)
        finding = result.findings[0]
        self.assertEqual(finding.source_id, 'S1')
        self.assertEqual(finding.source, next(iter(sources)))
        saved = finding_record(finding, 'F1')
        self.assertEqual(saved['supporting_text'], findings[0].supporting_text)
        self.assertNotIn(findings[0].supporting_text, render_research(result, sources=sources))
        # CrewAI retry serialization must not drop the private evidence.
        restored = ResearchResult.model_validate_json(result.model_dump_json())
        self.assertEqual(restored.findings[0].supporting_text, finding.supporting_text)

    def test_archive_year_cannot_turn_an_old_figure_into_current_data(self):
        sources = self.sources()
        finding = self.finding(summary='Markkinan arvo on 895 miljoonaa euroa vuonna 2026.', period=None, period_support='')
        result, _ = filter_excerpt_findings(ResearchResult(topic='Test', findings=[finding]), sources)
        reviewer = Mock()
        reviewer.call.return_value = {'assessments': [{'finding_id': 'F1', 'supported': True,
            'scope_supported': True, 'single_source_supported': True, 'reason': 'Reviewer incorrectly accepted.'}]}
        checked, excluded = assess_findings(result, sources, {}, reviewer, _repair=False)
        self.assertEqual(checked.findings, [])
        self.assertEqual(len(excluded), 1)
        self.assertFalse(next(iter(sources.values()))['finding_reviews'][0]['scope_supported'])

    def test_unknown_observation_period_stays_unknown_despite_publication_date(self):
        sources = self.sources()
        finding = self.finding(period=None, period_support='')
        result, _ = filter_excerpt_findings(ResearchResult(topic='Test', findings=[finding]), sources)
        self.assertIsNone(result.findings[0].period)

    def test_new_task_rejects_url_output_but_saved_url_models_remain_loadable(self):
        from crewai.tasks.task_output import TaskOutput
        from src.ai_research_assistant.crew import AiResearchAssistant
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test', 'SERPER_API_KEY': 'test'}):
            assistant = AiResearchAssistant()
            old = self.finding(source='https://example.test/')
            output = TaskOutput(description='Test', agent='Researcher', raw='', pydantic=ResearchResult(topic='Test', findings=[old]))
            self.assertFalse(assistant.check_research(output)[0])
            output.pydantic = ResearchResult(topic='Test', findings=[self.finding()])
            self.assertTrue(assistant.check_research(output)[0])

    def test_real_task_keeps_private_support_and_resolves_id_in_context(self):
        from crewai import Agent
        from src.ai_research_assistant.crew import AiResearchAssistant
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test', 'SERPER_API_KEY': 'test'}):
            assistant = AiResearchAssistant()
            assistant.search_tool.sources.update(self.sources())
            assistant.checkpoint = Mock()
            assistant.reviewer = Mock()
            assistant.reviewer.call.return_value = {'assessments': [{'finding_id': 'F1', 'supported': True,
                'scope_supported': True, 'single_source_supported': True, 'reason': 'Supported.'}]}
            with patch.object(Agent, 'execute_task', return_value=ResearchResult(topic='Test', findings=[self.finding()])):
                output = assistant.research_task().execute_sync()
            self.assertIn('[S1]', output.raw)
            self.assertNotIn('The market was', output.raw)
            saved = next(iter(assistant.checkpoint.call_args.kwargs['sources'].values()))
            self.assertEqual(saved['research_findings'][0]['period_support'], '895 million euros in 2023')
