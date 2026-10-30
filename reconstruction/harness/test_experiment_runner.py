import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import tempfile
import unittest
from experiment_runner import run_trial


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.source = self.root / 'src'; self.source.mkdir()
        (self.source / 'value').write_text('one')
        self.command = [sys.executable, '-c', "from pathlib import Path; import sys; Path(sys.argv[2], 'result').write_text(Path(sys.argv[1], 'value').read_text())", '{source}', '{out}']
        self.out = self.root / 'results'

    def run_trial(self, command=None, **kw):
        return run_trial(self.source, command or self.command, self.out, **kw)

    def test_resume_and_source_invalidation(self):
        first = self.run_trial(); self.assertEqual(first['status'], 'pass')
        self.assertTrue(self.run_trial()['reused'])
        (self.source / 'value').write_text('two')
        second = self.run_trial(); self.assertFalse(second['reused'])
        self.assertNotEqual(first['attempt'], second['attempt'])
        self.assertTrue((self.out / first['attempt']).exists())

    def test_artifact_tampering_invalidates_resume(self):
        first = self.run_trial()
        (self.out / first['attempt'] / 'output/result').write_text('tampered')
        self.assertFalse(self.run_trial()['reused'])

    def test_input_change_invalidates_resume(self):
        tool = self.root / 'tool'; tool.write_text('v1')
        self.run_trial(inputs=[tool]); self.assertTrue(self.run_trial(inputs=[tool])['reused'])
        tool.write_text('v2'); self.assertFalse(self.run_trial(inputs=[tool])['reused'])

    def test_fail_error_timeout_distinguished(self):
        for code, status in [(1, 'fail'), (2, 'error')]:
            self.assertEqual(self.run_trial([sys.executable, '-c', f'raise SystemExit({code})'])['status'], status)
        result = self.run_trial([sys.executable, '-c', 'import time; time.sleep(30)'], timeout=.05)
        self.assertEqual(result['status'], 'error'); self.assertEqual(result['reason'], 'timeout')

    def test_source_mutation_rejects_result(self):
        result = self.run_trial([sys.executable, '-c', "from pathlib import Path; import sys; Path(sys.argv[1], 'value').write_text('changed')", '{source}'])
        self.assertEqual(result['status'], 'error')
        self.assertEqual((self.source / 'value').read_text(), 'one')

    def test_concurrent_same_trial_reuses_single_attempt(self):
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda _: self.run_trial(), range(3)))
        self.assertEqual(len({r['attempt'] for r in results}), 1)
        self.assertEqual(sum(not r['reused'] for r in results), 1)

    def test_unsafe_inputs_rejected(self):
        with self.assertRaises(ValueError): run_trial(self.source, self.command, self.source / 'out')
        (self.source / 'link').symlink_to(self.source / 'value')
        with self.assertRaises(ValueError): self.run_trial()


if __name__ == '__main__': unittest.main()
