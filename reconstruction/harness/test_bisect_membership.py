import unittest
import bisect_membership
from bisect_membership import narrow


class BisectTests(unittest.TestCase):
    def test_finds_adjacent_boundary(self):
        result = narrow(list(range(20)), lambda i: 'pass' if i < 13 else 'fail', 8)
        self.assertEqual(result['status'], 'boundary-found')
        self.assertEqual(result['last_passing'], 12)
        self.assertEqual(result['first_failing_bound'], 13)
        self.assertLessEqual(len(result['tested']), 8)

    def test_build_error_does_not_become_culprit(self):
        result = narrow(['a', 'b', 'c'], lambda x: {'a':'pass','b':'error','c':'fail'}[x], 10)
        self.assertEqual(result['status'], 'unresolved')
        self.assertEqual(result['possible_first_failures'], ['b', 'c'])

    def test_budget_and_invalid_endpoints(self):
        result = narrow(list(range(10)), lambda i: 'pass' if i < 5 else 'fail', 2)
        self.assertEqual(result['status'], 'unresolved'); self.assertEqual(len(result['tested']), 2)
        self.assertEqual(narrow([0, 1], lambda i: 'error', 2)['status'], 'invalid-endpoints')

    def test_oracle_config_loads_as_utf8_independent_of_host_locale(self):
        # An oracle whose command carries a non-ASCII label (here U+2192)
        # cannot be decoded by locale-default readers on hosts whose ANSI
        # code page is not UTF-8 (cp949 raises on byte 0xe2).
        import json
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temporary:
            oracle = Path(temporary) / 'oracle.json'
            oracle.write_bytes(json.dumps({'command': ['rustc'], 'note': 'SOL \u2192 tokens'}).encode('utf-8'))
            config = bisect_membership.load_oracle(oracle)
        self.assertEqual(config['note'], 'SOL \u2192 tokens')


if __name__ == '__main__': unittest.main()
