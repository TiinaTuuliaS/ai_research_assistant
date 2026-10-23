import json
import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.ai_research_assistant.analysis_result import Comparison
from src.ai_research_assistant.research_contract import bind_entities
from src.ai_research_assistant.research_result import ResearchFinding, ResearchResult
from src.ai_research_assistant.question_fit import assess_question_fit
from src.ai_research_assistant.report_fallback import compose_fallback
from src.report_outcome import report_status
from tests.test_analysis_result import analysis_fixture


class WorkflowReliabilityTests(unittest.TestCase):
    def test_bad_comparison_is_local_in_actual_guardrail_for_distinct_topics(self):
        from crewai.tasks.task_output import TaskOutput
        from src.ai_research_assistant.crew import AiResearchAssistant
        cases = json.loads((Path(__file__).parent / 'fixtures/comparison_reliability.json').read_text(encoding='utf-8'))
        # A third domain uses the same contract without provider-specific rules.
        cases.append({'topic': 'Projektinhallintaohjelmistot', 'findings': [
            dict(finding_id='F1', source='https://a.test/', source_id='S1', entity='Tool A', supporting_text='Price 10'),
            dict(finding_id='F2', source='https://b.test/', source_id='S2', entity='Tool B', supporting_text='Price 20')]})
        for case in cases:
            for defect in ('one_side', 'unknown_finding', 'unknown_entity'):
                with self.subTest(topic=case['topic'], defect=defect), patch.dict(os.environ, {'OPENAI_API_KEY': 'test', 'SERPER_API_KEY': 'test'}):
                    assistant = AiResearchAssistant()
                    assistant.brief = dict(topic=case['topic'], research_type='competition')
                    ledger = case['findings']
                    bind_entities(ledger)
                    assistant.search_tool.sources['https://ledger.test/'] = {'research_findings': ledger}
                    first, second = ledger[:2]
                    result = analysis_fixture(topic=case['topic'], mode='competition', ids=[first['finding_id']])
                    valid = Comparison(competitor_id=first['entity_id'], feature='Published terms', status='unknown', finding_ids=[first['finding_id']], limitation='Other terms missing')
                    bad = Comparison(competitor_id='E999' if defect == 'unknown_entity' else first['entity_id'], feature='Unsupported difference', status='evidenced_difference', finding_ids=['F999'] if defect == 'unknown_finding' else [first['finding_id']], limitation='Missing other side')
                    result.comparisons = [valid, bad]
                    output = TaskOutput(description='Test', agent='Analyst', raw='', pydantic=result)
                    ok, _ = assistant.check_analysis(output)
                    self.assertTrue(ok)
                    self.assertEqual([c.feature for c in output.pydantic.comparisons], ['Published terms'])
                    self.assertEqual(output.pydantic.answer.finding_ids, [first['finding_id']])
                    self.assertNotIn('Unsupported difference', output.raw)
                    self.assertIn('jätettiin pois', result.gaps[-1])

    def test_partial_fit_handoff_preserves_price_without_requiring_other_criteria(self):
        for topic in ('Ravintolat', 'Työtilat', 'Ohjelmistot'):
            finding = ResearchFinding(title='Price', summary='Provider price is 10 euros.', source='S1', supporting_text='Price 10', evidence_kind='price', relevance=9, entity='Provider', area='', period='', limitations=['Feature details missing'])
            reviewer = Mock()
            reviewer.call.return_value = {'assessments': [{'index': 0, 'fit': 'direct', 'reason': 'Answers price criterion; features missing.'}]}
            checked, notes, query = assess_question_fit(ResearchResult(topic=topic, findings=[finding]), {'goal': 'Compare prices and features.'}, reviewer)
            self.assertEqual(checked.findings[0].question_fit, 'direct')
            self.assertEqual(checked.findings[0].summary, finding.summary)
            self.assertFalse(notes)
            self.assertFalse(query)
            self.assertIn('AT LEAST ONE', reviewer.call.call_args.args[0][0]['content'])

    def test_fallback_preserves_all_nine_saved_restaurant_observations(self):
        case = json.loads((Path(__file__).parent / 'fixtures/comparison_reliability.json').read_text(encoding='utf-8'))[0]
        sources = {f['source']: {'title': f['title'], 'research_findings': [f]} for f in case['findings']}
        report = compose_fallback({'research_type': 'competition'}, sources, [])
        self.assertEqual(report_status(report), 'limited')
        for finding in case['findings']:
            self.assertIn(finding['summary'], report)

    def test_archived_limited_report_is_not_reported_as_success(self):
        self.assertEqual(report_status('**Rajattu raportti:** Saved'), 'limited')
        self.assertEqual(report_status('**Limited report:** Saved'), 'limited')
        self.assertEqual(report_status('Normal report'), 'completed')
        self.assertEqual(report_status('', 'failed'), 'failed')
