import unittest

from scripts.evaluate import normal, score


def row(value=1, unit='mg/dL', reference_range='0 - 2', test_name='CRP'):
    return dict(test_name=test_name, value=value, unit=unit, reference_range=reference_range)


class EvaluationTests(unittest.TestCase):
    def test_equivalent_number_formats(self):
        self.assertEqual(normal('2,29,000', 'value'), normal(229000, 'value'))
        self.assertEqual(normal('0.50', 'value'), normal(0.5, 'value'))

    def test_clinical_distinctions_are_preserved(self):
        for a, b in [('<0.5', '0.5'), ('Negative', None), ('2-3', '23'), ('0', None)]:
            self.assertNotEqual(normal(a, 'value'), normal(b, 'value'))
        self.assertNotEqual(normal('mg/dL', 'unit'), normal('mmol/L', 'unit'))

    def test_missing_and_extra_rows(self):
        result = score([row(), row(test_name='TSH')], [row(), row(test_name='Unknown')])
        self.assertEqual(result['fully_correct'], 1)
        self.assertEqual(result['matched'], 1)
        self.assertEqual(len(result['extra_rows']), 1)

    def test_wrong_result_is_not_a_correct_row(self):
        result = score([row()], [row(value=10)])
        self.assertEqual(result['fully_correct'], 0)
        self.assertEqual(result['field_correct']['unit'], 1)

    def test_repeated_names_match_in_order(self):
        result = score([row(1), row(2)], [row(2), row(1)])
        self.assertEqual(result['fully_correct'], 0)


if __name__ == '__main__':
    unittest.main()
