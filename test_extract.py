import json
import unittest
from pathlib import Path

import extract


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


if __name__ == '__main__':
    unittest.main()
