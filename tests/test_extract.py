import json
import io
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from lab_extractor import pipeline as extract
from lab_extractor.schemas import LabReport


def response(result, finish='STOP'):
    return {'candidates': [{'finishReason': finish, 'content': {'parts': [{'text': json.dumps(result)}]}}]}


class ExtractionTests(unittest.TestCase):
    def test_preserves_non_numeric_and_missing_results(self):
        values = ['Negative', 'Present (+)', '< 0.5', '2-3', '2,29,000', None, 0]
        data = {'tests': [dict(test_name='Example', value=v, unit=None, reference_range=None) for v in values]}
        self.assertEqual(extract.parse_response(response(data)), data)

    def test_rejects_partial_or_blocked_response(self):
        for finish in ['MAX_TOKENS', 'SAFETY', None]:
            with self.subTest(finish=finish), self.assertRaises(RuntimeError):
                extract.parse_response(response({'tests': []}, finish))
        with self.assertRaises(RuntimeError):
            extract.parse_response({'candidates': []})

    def test_rejects_schema_invalid_results(self):
        for data in [{'tests': [{}]}, {'tests': 'wrong'}, {'tests': [dict(test_name='', value=1, unit=None, reference_range=None)]}]:
            with self.subTest(data=data), self.assertRaises(RuntimeError):
                extract.parse_response(response(data))

    def test_required_nullable_fields_and_strict_types(self):
        valid = dict(test_name='CRP', value='<0.5', unit=None, reference_range=None)
        for missing in ['value', 'unit', 'reference_range']:
            row = dict(valid)
            del row[missing]
            with self.subTest(missing=missing), self.assertRaises(RuntimeError):
                extract.parse_response(response({'tests': [row]}))
        for field, value in [('test_name', 42), ('test_name', '  '), ('value', True),
                             ('value', {}), ('unit', 1), ('reference_range', [])]:
            with self.subTest(field=field, value=value), self.assertRaises(RuntimeError):
                extract.parse_response(response({'tests': [{**valid, field: value}]}))

    def test_numeric_strings_are_not_coerced(self):
        row = dict(test_name='Specific Gravity', value='1.020', unit=None, reference_range=None)
        result = extract.parse_response(response({'tests': [row]}))
        self.assertIsInstance(result['tests'][0]['value'], str)
        self.assertEqual(result['tests'][0]['value'], '1.020')

    def test_generated_schema_is_sent_to_gemini(self):
        success = io.BytesIO(json.dumps(response({'tests': []})).encode())
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-only'}), \
             patch('lab_extractor.pipeline.load_pages', return_value=[]), \
             patch('lab_extractor.pipeline.urllib.request.urlopen', return_value=success) as call:
            extract.extract(Path('unused.pdf'))
        request = call.call_args.args[0]
        config = json.loads(request.data)['generationConfig']
        self.assertEqual(config['responseMimeType'], 'application/json')
        self.assertEqual(config['responseJsonSchema'], LabReport.model_json_schema())
        fields = config['responseJsonSchema']['$defs']['LabTest']['required']
        self.assertEqual(set(fields), {'test_name', 'value', 'unit', 'reference_range'})

    def test_rejects_non_json_and_nonfinite_numbers(self):
        for text in ['not JSON', '{"tests": [', '{"tests":[{"test_name":"X","value":NaN,"unit":null,"reference_range":null}]}']:
            with self.subTest(text=text), self.assertRaises(RuntimeError):
                extract.parse_response({'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': text}]}}]})

    def test_all_pdf_pages_are_passed_in_order(self):
        parts = extract.load_pages(Path('reports/report_11.pdf'))
        self.assertEqual([p['text'] for p in parts if 'text' in p], ['Page 1', 'Page 2'])
        self.assertEqual(sum('inlineData' in p for p in parts), 2)

    def test_missing_and_unsupported_inputs(self):
        for path in [Path('reports/does-not-exist.pdf'), Path('schema.json')]:
            with self.subTest(path=path), self.assertRaises(RuntimeError):
                extract.load_pages(path)

    def test_transient_http_failure_retries_once(self):
        failure = urllib.error.HTTPError('https://example.invalid', 503, 'Unavailable', {}, None)
        success = io.BytesIO(json.dumps(response({'tests': []})).encode())
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-only'}), \
             patch('lab_extractor.pipeline.load_pages', return_value=[]), \
             patch('lab_extractor.pipeline.urllib.request.urlopen', side_effect=[failure, success]) as call, \
             patch('lab_extractor.pipeline.time.sleep'):
            self.assertEqual(extract.extract(Path('unused.pdf')), {'tests': []})
            self.assertEqual(call.call_count, 2)

    def test_auth_failure_does_not_retry(self):
        failure = urllib.error.HTTPError('https://example.invalid', 403, 'Forbidden', {}, None)
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-only'}), \
             patch('lab_extractor.pipeline.load_pages', return_value=[]), \
             patch('lab_extractor.pipeline.urllib.request.urlopen', side_effect=failure) as call:
            with self.assertRaisesRegex(RuntimeError, 'HTTP 403'):
                extract.extract(Path('unused.pdf'))
            self.assertEqual(call.call_count, 1)


if __name__ == '__main__':
    unittest.main()
