import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from build_e2e import AuditedProvider, provider_settings, SourceWindowProvider


class ProviderSettingsTests(unittest.TestCase):
    def test_provider_choice_is_explicit_without_fallback_or_key_rotation(self):
        self.assertEqual('gemini',provider_settings({})['provider'])
        gemini=provider_settings({'online_provider':'gemini'})
        groq=provider_settings({'online_provider':'groq'})
        self.assertEqual(32768,gemini['extended_output_tokens'])
        self.assertEqual(4096,groq['extended_output_tokens'])
        self.assertEqual(2048,groq['normal_output_tokens'])
        self.assertIsNone(groq['thinking_level'])
        self.assertEqual('GROQ_API_KEY_1',groq['key_env'])
        self.assertEqual('qwen/qwen3.8-27b',groq['model'])
        with self.assertRaises(ValueError):provider_settings({'online_provider':'automatic'})


class SourceWindowTests(unittest.TestCase):
    def test_explicit_whole_file_view_tracks_created_source_without_scope_or_cap_expansion(self):
        with tempfile.TemporaryDirectory() as directory:
            wrapper=SourceWindowProvider(object(),Path(directory),{'created.ts':'all'},max_context_bytes=1024)
            context={'files':[{'path':'created.ts','content':'','sha256':'absent'},
                              {'path':'private.ts','content':'PRIVATE','sha256':'private'}]}
            self.assertEqual([],json.loads(wrapper.project(json.dumps(context)))['files'][0]['excerpts'])
            context['files'][0].update(content='export const value=1;\n',sha256='current')
            result=json.loads(wrapper.project(json.dumps(context)))
            self.assertEqual('export const value=1;\n',result['files'][0]['excerpts'][0]['content'])
            self.assertEqual('current',result['files'][0]['sha256'])
            self.assertNotIn('PRIVATE',json.dumps(result))
            context['files'][0]['content']='x'*2000
            with self.assertRaises(ValueError):wrapper.project(json.dumps(context))
            with self.assertRaises(ValueError):
                SourceWindowProvider(object(),Path(directory),{'unselected.ts':'all'}).project(json.dumps(context))

    def test_diagnostic_excerpt_preserves_identity_feedback_and_local_full_output(self):
        output='START'+'x'*6000+'END'
        original={'files':[], 'diagnostics':{'output':output,'task':'task-id','evidence':'evidence-id','proposal_review':'Keep this exact review'}}
        with tempfile.TemporaryDirectory() as directory:
            wrapper=SourceWindowProvider(object(),Path(directory),{},max_diagnostic_bytes=512)
            diagnostic=json.loads(wrapper.project(json.dumps(original)))['diagnostics']
            self.assertLessEqual(len(diagnostic['output'].encode()),512)
            self.assertTrue(diagnostic['output'].startswith('START'))
            self.assertTrue(diagnostic['output'].endswith('END'))
            self.assertEqual(hashlib.sha256(output.encode()).hexdigest(),diagnostic['full_output_sha256'])
            self.assertEqual(len(output.encode()),diagnostic['full_output_bytes'])
            self.assertEqual('bounded_excerpt',diagnostic['output_view'])
            self.assertEqual('evidence-id',diagnostic['evidence'])
            self.assertEqual('Keep this exact review',diagnostic['proposal_review'])
            self.assertEqual(output,original['diagnostics']['output'])
            for limit in (True,255,8001,'512'):
                with self.assertRaises(ValueError):
                    SourceWindowProvider(object(),Path(directory),{},max_diagnostic_bytes=limit)

    def test_smaller_reviewed_byte_cap_blocks_before_any_provider_call(self):
        class Provider:
            calls = 0
            def complete(self, *args):
                self.calls += 1
                raise AssertionError('Oversized payload must never leave the process')
        provider = Provider()
        context = json.dumps({'files': [{'path': 'source.ts', 'content': 'x' * 2000}]})
        with tempfile.TemporaryDirectory() as directory:
            wrapper = SourceWindowProvider(provider, Path(directory),
                {'source.ts': [[1, 1]]}, max_context_bytes=1024)
            with self.assertRaisesRegex(ValueError, 'reviewed byte cap'):
                wrapper.complete('system', context, {})
            from jarvis_runtime.responses import ContextBudgetExceeded, failure_code
            self.assertEqual('context_budget_exceeded',
                failure_code(ContextBudgetExceeded(), 'generation_failed', provider_failure=True))
            self.assertEqual(0, provider.calls)
            self.assertFalse((Path(directory) / 'source-views').exists())
            for limit in (True, 1023, 24001, '12000'):
                with self.assertRaises(ValueError):
                    SourceWindowProvider(provider, Path(directory), {}, max_context_bytes=limit)

    def test_outgoing_views_reduce_content_keep_hashes_and_never_mutate_full_context(self):
        context={'goal':'fix selected branch','files':[{'path':'source.ts','content':'first\nselected\nprivate-unused\n','sha256':'original','protected':False},
                   {'path':'test.ts','content':'protected source','sha256':'protected','protected':True}]}
        with tempfile.TemporaryDirectory() as directory:
            wrapper=SourceWindowProvider(object(),Path(directory),{'source.ts':[[2,2]]})
            sent=json.loads(wrapper.project(json.dumps(context)))
            self.assertEqual('selected\n',sent['files'][0]['excerpts'][0]['content'])
            self.assertEqual('original',sent['files'][0]['sha256'])
            self.assertTrue(sent['files'][1]['protected'])
            self.assertNotIn('private-unused',json.dumps(sent))
            self.assertIn('private-unused',context['files'][0]['content'])
            for views in ({'unselected':[[1,1]]},{'source.ts':[[1,99]]},{'source.ts':[[True,2]]}):
                with self.assertRaises(ValueError):SourceWindowProvider(object(),Path(directory),views).project(json.dumps(context))


class SafeProviderFailureTests(unittest.TestCase):
    def test_oversized_http_request_is_classified_without_private_body(self):
        from jarvis_runtime.responses import failure_code
        class RequestTooLarge(Exception): status_code=413
        result=failure_code(RequestTooLarge('private request body or key'), 'generation_failed', provider_failure=True)
        self.assertEqual('provider_http_413',result)
        self.assertNotIn('private',result)


class ProviderAuditTests(unittest.TestCase):
    def test_rate_limit_body_retains_only_bounded_delay_and_allowlisted_scope(self):
        class Limited(Exception):
            status_code = 429
            body = {'error': {'message': 'Tokens per day exceeded. Please try again in 1m2.5s. private-key private source'}}
        class Provider:
            def complete(self, *args): raise Limited('private exception')
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(Limited):
                AuditedProvider(Provider(), Path(directory)).complete('system', '{}', {})
            path = next((Path(directory) / 'provider-status').glob('*.json'))
            record = json.loads(path.read_text())
            self.assertEqual('tokens_per_day', record['rate_limit_scope'])
            self.assertEqual(62.5, record['retry_after_seconds'])
            self.assertNotIn('private', path.read_text())

    def test_bad_request_keeps_allowlisted_code_and_discards_failed_generation(self):
        class Rejected(Exception):
            status_code = 400
            body = {'error': {'code': 'json_validate_failed', 'failed_generation': 'private source'}}
        class Fixture:
            def complete(self, *args):
                raise Rejected('private message')
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(Rejected):
                AuditedProvider(Fixture(), Path(directory)).complete('system', '{}', {})
            path = next((Path(directory) / 'provider-status').glob('*.json'))
            self.assertEqual('json_validate_failed', json.loads(path.read_text())['code'])
            self.assertNotIn('private', path.read_text())

    def test_rate_limit_retains_only_numeric_retry_header_without_retrying(self):
        from types import SimpleNamespace
        class Limited(Exception):
            status_code = 429
        class Fixture:
            calls = 0
            def complete(self, *args):
                self.calls += 1
                error = Limited('private exception body and credentials')
                error.response = SimpleNamespace(headers={'retry-after': '91.5', 'authorization': 'private-key'})
                raise error
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture()
            with self.assertRaises(Limited):
                AuditedProvider(fixture, Path(directory)).complete('private source', '{}', {})
            self.assertEqual(1, fixture.calls)
            path = next((Path(directory) / 'provider-status').glob('*.json'))
            record = json.loads(path.read_text())
            self.assertEqual(91.5, record['retry_after_seconds'])
            self.assertFalse(record['automatic_retry'])
            self.assertNotIn('private', path.read_text())

    def test_received_text_is_retained_before_validation_without_key_or_usage_dump(self):
        class Fixture:
            model='fixture'; api_key='private-provider-key'
            def complete(self,*args):return 'malformed model text',{'total_tokens':12}
        with tempfile.TemporaryDirectory() as directory:
            provider=AuditedProvider(Fixture(),Path(directory))
            self.assertEqual('malformed model text',provider.complete('system','{"files":[]}',{})[0])
            records=list((Path(directory)/'model-responses').glob('*.json'))
            self.assertEqual(1,len(records));record=json.loads(records[0].read_text())
            self.assertEqual('untrusted_model_response',record['kind'])
            self.assertEqual('malformed model text',record['text'])
            self.assertEqual(hashlib.sha256(record['text'].encode()).hexdigest(),record['text_sha256'])
            self.assertNotIn('private-provider-key',records[0].read_text())
            self.assertNotIn('usage',record)

    def test_provider_exceptions_are_never_written_and_oversized_responses_are_digest_only(self):
        class Failure:
            model='fixture'
            def complete(self,*args):raise RuntimeError('private-exception-detail')
        class Large:
            model='fixture'
            def complete(self,*args):return 'x'*131073,{}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with self.assertRaises(RuntimeError):AuditedProvider(Failure(),root).complete('system','{}',{})
            self.assertFalse((root/'model-responses').exists())
            AuditedProvider(Large(),root).complete('system','{}',{})
            record=json.loads(next((root/'model-responses').glob('*.json')).read_text())
            self.assertTrue(record['digest_only']);self.assertNotIn('text',record)


if __name__=='__main__':unittest.main()
