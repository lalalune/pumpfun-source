import unittest
from pair_candidates import report, body_groups


class PairingTests(unittest.TestCase):
    def setUp(self):
        self.ranked = [(1., .8, 10, 8, 'a'), (1., .7, 20, 8, 'b')]
        self.groups = {(10, 8): [{'symbol': 'a'}, {'symbol': 'alias'}], (20, 8): [{'symbol': 'b'}]}

    def test_ties_and_aliases_visible(self):
        result = report(self.ranked, self.groups)
        self.assertTrue(result['top_ratio_tied'])
        self.assertTrue(result['selected_body_ambiguous'])
        self.assertEqual(len(result['candidates']), 2)

    def test_explicit_selection_and_bad_override(self):
        result = report(self.ranked, self.groups, 'b')
        self.assertEqual(result['selected']['start'], 20)
        self.assertEqual(result['selection'], 'explicit-symbol')
        with self.assertRaises(ValueError): report(self.ranked, self.groups, 'missing')
        with self.assertRaises(ValueError): report([], {})

    def test_single_result_has_no_invented_margin(self):
        self.assertIsNone(report(self.ranked[:1], self.groups)['top_ratio_margin'])

    def test_normalized_body_groups_include_all_aliases(self):
        class Candidate:
            funcs = [(0, 8, 'a'), (8, 8, 'b'), (8, 8, 'alias')]
            secs = {}
            def fn(self, start, size): return b'\x95' + bytes(7)
        groups = body_groups(Candidate())
        self.assertEqual([x['symbol'] for x in groups[(0, 8)]], ['a', 'b', 'alias'])
        self.assertEqual(groups[(0, 8)], groups[(8, 8)])


if __name__ == '__main__': unittest.main()
