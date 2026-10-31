"""An interrupted append must not swallow the next successful AMM ledger write."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent / 'amm_sell'


class TornTailAppendTests(unittest.TestCase):
    def run_tool(self, root, *arguments):
        return subprocess.run([sys.executable, '-B', *arguments],
                              env=dict(os.environ, AMM_SELL_SWARM=str(root)),
                              text=True, capture_output=True, timeout=20)

    def append(self, root, writer):
        if writer == 'note':
            return self.run_tool(root, str(HERE / 'attempts.py'), 'note',
                                 '--lane', 'new', '--approach', 'append',
                                 '--kind', 'finding', '--text', 'new complete record')
        code = ('import sys; sys.path.insert(0, sys.argv[1]); import try_sell; '
                'try_sell.locked_append({"schema":"amm-sell-attempt-v1",'
                '"lane":"new","approach":"append","hypothesis":"new complete record",'
                '"status":"build_failed"})')
        return self.run_tool(root, '-c', code, str(HERE))

    def test_both_writers_keep_new_rows_readable_after_an_unterminated_tail(self):
        # Also preserve a complete last row that merely lacks its final LF.
        prior = {'schema': 'amm-sell-note-v1', 'lane': 'old', 'approach': 'old',
                 'kind': 'prior', 'text': 'old complete record'}
        for writer in ('note', 'build'):
            for tail in (b'{"schema":"amm-sell-attempt-v1","hypothesis":"cut',
                         json.dumps(prior).encode(), b''):
                with self.subTest(writer=writer, tail=tail), tempfile.TemporaryDirectory() as folder:
                    root = Path(folder)
                    log = root / 'ATTEMPTS.jsonl'
                    log.write_bytes(tail)
                    result = self.append(root, writer)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    readback = self.run_tool(root, str(HERE / 'attempts.py'), 'grep', 'new complete record')
                    self.assertEqual(readback.returncode, 0, readback.stderr)
                    self.assertIn('new/append', readback.stdout, readback.stderr)
                    self.assertTrue(log.read_bytes().startswith(tail), 'existing evidence was rewritten')
                    if tail == json.dumps(prior).encode():
                        self.assertEqual(json.loads(log.read_text().splitlines()[0]), prior)

    def test_normal_line_terminated_log_has_no_extra_blank_line(self):
        for writer in ('note', 'build'):
            with self.subTest(writer=writer), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                prior = b'{"schema":"unknown"}\n'
                (root / 'ATTEMPTS.jsonl').write_bytes(prior)
                result = self.append(root, writer)
                self.assertEqual(result.returncode, 0, result.stderr)
                lines = (root / 'ATTEMPTS.jsonl').read_bytes().splitlines()
                self.assertEqual(len(lines), 2)
                self.assertTrue(all(lines))


if __name__ == '__main__':
    unittest.main()
