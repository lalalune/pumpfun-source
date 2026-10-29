"""Fail-closed mutations of retained traces and recipes; no compiler execution."""
from pathlib import Path
import copy
import importlib.util
import unittest

P = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('field_verify', P / 'verify.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class EvidenceMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.active = v.text('fields/repaired-scheduler1-priority1/stderr.log')
        cls.passive = v.text('fields/repaired-scheduler0-priority0/stderr.log')
        cls.launch = v.record('fields/repaired-scheduler1-priority1/launch.json')
        cls.base = v.record('scheduler/stock-frequency/launch.json')
        cls.flags = cls.launch['command'][11:]

    def reject(self, before, after, message):
        self.assertIn(before, self.active)
        altered = self.active.replace(before, after, 1)
        with self.assertRaisesRegex(ValueError, message):
            v.fields(altered, True, True)

    def test_recorded_controls(self):
        self.assertEqual(v.fields(self.active, True, True)['interventions'], 2)
        self.assertEqual(v.fields(self.passive, False, False)['interventions'], 0)

    def test_forged_priority(self):
        self.reject('priority=2147483820', 'priority=2147483819', 'priority calculation')

    def test_wrong_interval_endpoint(self):
        self.reject('end=6384r', 'end=6400r', 'interval/size')

    def test_unqualified_hint(self):
        self.reject('preference=0', 'preference=1', 'unhinted')

    def test_duplicate_priority_event(self):
        line = next(x for x in self.active.splitlines() if x.startswith('FIELD_PROBE enqueue '))
        self.reject(line, line + '\n' + line, 'unique ordered')

    def test_missing_intervention(self):
        line = next(x for x in self.active.splitlines() if x.startswith('V3_FIELD_COUNTERFACTUAL'))
        self.reject(line + '\n', '', 'intervention count')

    def test_unknown_intervention(self):
        with self.assertRaisesRegex(ValueError, 'intervention count'):
            v.fields(self.active + '\nV3_FIELD_COUNTERFACTUAL unparsed\n', True, True)

    def test_changed_intervention(self):
        self.reject('replacement=2147483816', 'replacement=2147483817', 'intervention count')

    def test_wrong_color(self):
        self.reject('assigning %101 to $r1:', 'assigning %101 to $r2:', 'allocation order')

    def test_forged_interference(self):
        self.reject('physical=$r1 interference=1', 'physical=$r1 interference=0', 'interference')

    def test_no_intervention_in_passive_control(self):
        line = next(x for x in self.active.splitlines() if x.startswith('V3_FIELD_COUNTERFACTUAL'))
        with self.assertRaisesRegex(ValueError, 'intervention count'):
            v.fields(self.passive + '\n' + line + '\n', False, False)

    def test_literal_recipe(self):
        v.recipe(self.launch, self.base, self.flags, v.TOOLS['fields2'])
        changed = copy.deepcopy(self.launch)
        changed['command'].append('-post-RA-scheduler=true')
        with self.assertRaisesRegex(ValueError, 'literal command/environment'):
            v.recipe(changed, self.base, self.flags, v.TOOLS['fields2'])

    def test_changed_environment(self):
        changed = copy.deepcopy(self.launch)
        changed['environment']['EXTRA_UNRECORDED_SETTING'] = '1'
        with self.assertRaisesRegex(ValueError, 'literal command/environment'):
            v.recipe(changed, self.base, self.flags, v.TOOLS['fields2'])

    def test_wrong_compiler_or_input(self):
        for key in ['tool_sha256', 'input_sha256']:
            changed = copy.deepcopy(self.launch)
            changed[key] = '0' * 64
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'pinned compiler/input'):
                v.recipe(changed, self.base, self.flags, v.TOOLS['fields2'])

    def test_pointer_filter_keeps_probabilities(self):
        analyzer = v.module('scheduler/controllers/analyze.py')
        before = 'BasicBlock:ch<bb 0x1234> probability=0x80000000\n'
        after = analyzer.pointers(before)
        self.assertEqual(after, 'BasicBlock:ch<bb <ADDRESS>> probability=0x80000000\n')
        self.assertNotEqual(after, analyzer.pointers(before.replace('0x80000000', '0x40000000')))

    def test_log_filter_keeps_real_instructions(self):
        a = 'FIELD_PROBE candidate example\nassigning %101 to $r1:\n'
        self.assertEqual(v.strip_field_logs(a), 'assigning %101 to $r1:\n')
        self.assertNotEqual(v.strip_field_logs(a), v.strip_field_logs(a.replace('$r1', '$r2')))


if __name__ == '__main__':
    unittest.main()
