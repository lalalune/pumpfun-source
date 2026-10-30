import unittest
from minimize_experiment import minimize


class MinimizeTests(unittest.TestCase):
    def test_finds_necessary_unit(self):
        result = minimize(8, lambda items: 'pass' if 3 in items else 'fail', 30)
        self.assertEqual(result['selected'], [3]); self.assertTrue(result['one_minimal'])

    def test_interacting_units_remain(self):
        result = minimize(6, lambda items: 'pass' if {1, 4} <= set(items) else 'fail', 30)
        self.assertEqual(result['selected'], [1, 4]); self.assertTrue(result['one_minimal'])

    def test_errors_and_budget_do_not_prove_minimality(self):
        result = minimize(2, lambda items: 'pass' if len(items) == 2 else 'error', 10)
        self.assertFalse(result['one_minimal']); self.assertEqual(result['selected'], [0, 1])
        result = minimize(8, lambda items: 'pass', 1)
        self.assertFalse(result['one_minimal']); self.assertEqual(len(result['tested']), 1)

    def test_empty_base_and_wrong_initial_predicate(self):
        self.assertEqual(minimize(2, lambda items: 'pass', 5)['selected'], [])
        self.assertEqual(minimize(2, lambda items: 'fail', 5)['status'], 'initial-predicate-not-met')
        self.assertEqual(minimize(3, lambda items: 'fail' if 1 in items else 'pass', 10, 'fail')['selected'], [1])


if __name__ == '__main__': unittest.main()
