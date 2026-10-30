import unittest
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


if __name__ == '__main__': unittest.main()
