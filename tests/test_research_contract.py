import json
import unittest
from pathlib import Path
from unittest.mock import Mock

from src.ai_research_assistant.research_contract import parse_research, bind_entities, resolve_comparisons
from src.ai_research_assistant.research_result import ResearchFinding, ResearchResult
from src.ai_research_assistant.evidence import assess_findings, filter_excerpt_findings
from test_analysis_result import analysis_fixture


def record(**changes):
    return dict(title='Palvelu', summary='Yritys tarjoaa huoltoa.', source='S1',
        supporting_text='Tarjoamme huoltoa.', period_support='', relevance=8,
        evidence_kind='offering', trend_kind='snapshot', entity='Yritys', area='',
        period='', limitations=['Kysyntä ei selviä.'], **changes)


class ResearchContractTests(unittest.TestCase):
    def test_invalid_classification_repairs_only_that_field_and_preserves_good_records(self):
        good = record()
        bad = {**good, 'source': 'S2', 'evidence_kind': 'infrastructure'}
        reviewer = Mock()
        reviewer.call.return_value = {'repairs': [{'index': 1, 'evidence_kind': 'other', 'trend_kind': 'forecast'}]}
        result, notes = parse_research(json.dumps({'topic': 'Latausverkosto', 'findings': [good, bad]}), reviewer)
        self.assertEqual(len(result.findings), 2)
        self.assertEqual(result.findings[0].summary, good['summary'])
        self.assertEqual(result.findings[1].evidence_kind, 'other')
        # The valid trend value must not change, even if repair proposes it.
        self.assertEqual(result.findings[1].trend_kind, 'snapshot')
        self.assertEqual(result.findings[1].source, 'S2')
        self.assertFalse(notes)
        reviewer.call.assert_called_once()

    def test_failed_repair_retains_other_valid_observations(self):
        reviewer = Mock()
        reviewer.call.side_effect = RuntimeError('Unavailable')
        result, notes = parse_research(json.dumps({'topic': 'Test', 'findings': [record(), {**record(), 'evidence_kind': 'invalid'}]}), reviewer)
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(len(notes), 1)

    def test_actual_task_exports_repaired_json_without_repeating_research(self):
        import os
        from unittest.mock import patch
        from crewai import Agent
        from src.ai_research_assistant.crew import AiResearchAssistant
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test', 'SERPER_API_KEY': 'test'}):
            assistant = AiResearchAssistant()
            assistant.search_tool.sources.update({f'https://s{i}.test/': {'source_id': f'S{i}',
                'snippet': 'Tarjoamme huoltoa.', 'page_status': 'unavailable'} for i in (1, 2)})
            assistant.reviewer = Mock()
            assistant.reviewer.call.return_value = {'repairs': [{'index': 1, 'evidence_kind': 'other', 'trend_kind': 'snapshot'}]}
            raw = json.dumps({'topic': 'Test', 'findings': [record(), {**record(), 'source': 'S2', 'evidence_kind': 'infrastructure'}]})
            with patch.object(Agent, 'execute_task', return_value=raw) as execute, \
                 patch('src.ai_research_assistant.crew.assess_findings', side_effect=lambda r, *args: (r, [])), \
                 patch('src.ai_research_assistant.crew.recover_unused_sources', side_effect=lambda r, *args: r):
                output = assistant.research_task().execute_sync()
            self.assertEqual(execute.call_count, 1)
            self.assertEqual(len(output.pydantic.findings), 2)
            self.assertEqual(output.pydantic.findings[1].evidence_kind, 'other')
            assistant.reviewer.call.assert_called_once()

    def test_company_reference_is_resolved_and_unknown_comparison_is_local(self):
        from src.ai_research_assistant.analysis_result import Comparison
        findings = [dict(finding_id='F1', entity='Radical Storage'), dict(finding_id='F2', entity=None)]
        bind_entities(findings)
        result = analysis_fixture(mode='competition', ids=['F1'])
        result.comparisons = [Comparison(competitor_id='E1', competitor='Wrong spelling', feature='Säilytys', status='unknown', finding_ids=['F1'], limitation='Ehdot avoimet.'),
            Comparison(competitor_id='E99', feature='Muu', status='unknown', finding_ids=['F2'], limitation='Tuntematon.')]
        resolve_comparisons(result, findings)
        self.assertEqual(len(result.comparisons), 1)
        self.assertEqual(result.comparisons[0].competitor, 'Radical Storage')
        self.assertEqual(findings[1]['entity_id'], '')
        self.assertIn('jätettiin pois', result.gaps[-1])
        self.assertEqual(result.answer.finding_ids, ['F1'])

    def test_source_vision_cannot_pass_as_current_use_even_if_support_flags_are_true(self):
        case = json.loads((Path(__file__).parent / 'fixtures/source_context_cases.json').read_text(encoding='utf-8'))['vision']
        finding = ResearchFinding.model_validate(case['finding'])
        sources = {case['url']: case['source']}
        result, _ = filter_excerpt_findings(ResearchResult(topic='Avustaja', findings=[finding]), sources)
        reviewer = Mock()
        reviewer.call.return_value = {'assessments': [dict(finding_id='F1', supported=True, scope_supported=True, single_source_supported=True, context_kind='forecast', context_preserved=True, reason='Lause löytyy.') ]}
        checked, notes = assess_findings(result, sources, {}, reviewer, _repair=False)
        self.assertFalse(checked.findings)
        self.assertTrue(notes)
        payload = json.loads(reviewer.call.call_args.args[0][1]['content'])
        self.assertIn('Visio 2040', payload['findings'][0]['own_evidence']['page_text'])

    def test_testimonial_must_retain_its_attribution(self):
        case = json.loads((Path(__file__).parent / 'fixtures/source_context_cases.json').read_text(encoding='utf-8'))['testimonial']
        finding = ResearchFinding.model_validate(case['finding'])
        sources = {case['url']: case['source']}
        result, _ = filter_excerpt_findings(ResearchResult(topic='Test', findings=[finding]), sources)
        reviewer = Mock()
        reviewer.call.return_value = {'assessments': [dict(finding_id='F1', supported=True, scope_supported=True, single_source_supported=True, context_kind='testimonial', context_preserved=False, reason='Yhden asiakkaan kokemus.') ]}
        checked, _ = assess_findings(result, sources, {}, reviewer, _repair=False)
        self.assertFalse(checked.findings)

    def test_valid_remote_degree_is_background_not_personal_tutoring_demand(self):
        from src.ai_research_assistant.question_fit import assess_question_fit
        finding = ResearchFinding.model_validate({**record(), 'summary': 'Oppilaitos tarjoaa tutkinnon verkossa.'})
        result = ResearchResult(topic='Henkilökohtainen ohjelmoinnin etätuki', findings=[finding])
        reviewer = Mock()
        reviewer.call.return_value = {'assessments': [{'index': 0, 'fit': 'background', 'reason': 'Tutkinnon toteutustapa ei mittaa lisäavun tarvetta.'}], 'followup_query': 'ammatillinen ohjelmointi opiskelijoiden lisäohjauksen tarve'}
        checked, notes, query = assess_question_fit(result, {'goal': 'Selvitä henkilökohtaisen lisäavun tarvetta.'}, reviewer)
        self.assertEqual(checked.findings[0].question_fit, 'background')
        self.assertEqual(checked.findings[0].summary, finding.summary)
        self.assertTrue(notes)
        self.assertIn('lisäohjauksen', query)

    def test_direct_fit_disables_followup_and_unknown_fit_does_not_discard_facts(self):
        from src.ai_research_assistant.question_fit import assess_question_fit
        result = ResearchResult(topic='Huoltojen hinnat', findings=[ResearchFinding.model_validate(record())])
        reviewer = Mock()
        reviewer.call.return_value = {'assessments': [{'index': 0, 'fit': 'direct', 'reason': 'Kuvaa kysyttyä palvelua.'}], 'followup_query': 'do not run'}
        checked, notes, query = assess_question_fit(result, {'goal': 'Vertaa huoltopalveluja.'}, reviewer)
        self.assertEqual(checked.findings[0].question_fit, 'direct')
        self.assertFalse(query)
        reviewer.call.return_value = {'assessments': []}
        checked, notes, query = assess_question_fit(result, {'goal': 'Test'}, reviewer)
        self.assertEqual(len(checked.findings), 1)
        self.assertEqual(checked.findings[0].question_fit, 'unassessed')
        self.assertTrue(notes)

    def test_question_gap_uses_one_remaining_search_and_preserves_new_source_identity(self):
        import os
        from unittest.mock import patch
        from crewai.tasks.task_output import TaskOutput
        from src.ai_research_assistant.crew import AiResearchAssistant
        from src.ai_research_assistant.tools.search_tool import SourceSearchTool
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test', 'SERPER_API_KEY': 'test'}):
            assistant = AiResearchAssistant()
            assistant.brief = {'goal': 'Selvitä henkilökohtaisen etätuen tarve.', 'language': 'suomi'}
            assistant.search_tool.sources['https://old.test/'] = {'source_id': 'S1', 'snippet': 'Tarjoamme huoltoa.', 'page_status': 'unavailable'}
            assistant.reviewer = Mock()
            assistant.reviewer.call.side_effect = [
                {'assessments': [{'index': 0, 'fit': 'background', 'reason': 'Taustatieto.'}], 'followup_query': 'opiskelijoiden henkilökohtaisen tuen tarve'},
                {'assessments': [{'index': 0, 'fit': 'background', 'reason': 'Taustatieto.'}, {'index': 1, 'fit': 'direct', 'reason': 'Kysymykseen vastaava havainto.'}]},
            ]
            def search(**kwargs):
                assistant.search_tool.sources['https://new.test/'] = {'source_id': 'S2', 'snippet': 'Tarjoamme huoltoa.', 'page_status': 'unavailable'}
                return {}
            def extract(result, *args, only_urls=None):
                if only_urls is None:
                    return result
                self.assertEqual(only_urls, {'https://new.test/'})
                added = ResearchFinding.model_validate({**record(), 'source': 'https://new.test/', 'source_id': 'S2'})
                return result.model_copy(update={'findings': [*result.findings, added]})
            output = TaskOutput(description='Test', agent='Researcher', raw='',
                pydantic=ResearchResult(topic='Etätuki', findings=[ResearchFinding.model_validate(record())]))
            with patch('src.ai_research_assistant.crew.assess_findings', side_effect=lambda r, *args: (r, [])), \
                 patch('src.ai_research_assistant.crew.recover_unused_sources', side_effect=extract), \
                 patch.object(SourceSearchTool, '_run', side_effect=search) as called:
                assistant.accept_research(output)
            called.assert_called_once()
            handoff = json.loads(output.raw)
            self.assertEqual(handoff['coverage']['direct'], 1)
            self.assertEqual(handoff['accepted_findings'][1]['source_id'], 'S2')
