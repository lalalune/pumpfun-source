"""Extern counters must distinguish real captured/compiled relocation symbols."""
from collections import Counter
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
LANE = ROOT / 'reconstruction/pump-main/lanes/callgraph-census'
sys.path.insert(0, str(LANE))
import census

ARCHIVE = ROOT / 'research/pump-multihop-sell-fees-20261029/build/candidate/symbols.so.gz'


class ExternalSymbolTests(unittest.TestCase):
    def test_retained_images_distinguish_same_count_and_preserve_equal_control(self):
        windows = {w['start']: (w['bytes'], []) for w in census.original_windows()}
        original = census.Image(ROOT / 'evidence/original/pump/deployed.so', windows)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'symbols.so'
            path.write_bytes(gzip.decompress(ARCHIVE.read_bytes()))
            functions = {s: (n, [name]) for s, n, name in census.candidate_functions(path)}
            candidate = census.Image(path, functions)
            # Symbol lookup must use the loaded image, even before its first query.
            path.unlink()
            self.assertEqual(original.external_counts(0x22a10),
                             Counter({'symbol:abort': 1, 'symbol:sol_log_': 2}))
            self.assertEqual(candidate.external_counts(0x2fb60), Counter({'symbol:sol_log_': 3}))
            expected = Counter({'symbol:abort': 1, 'symbol:sol_log_': 1})
            self.assertEqual(original.external_counts(0x72810), expected)
            self.assertEqual(candidate.external_counts(0x8c0e0), expected)
            # Repeated queries preserve that same loaded identity.
            self.assertEqual(candidate.external_counts(0x2fb60), Counter({'symbol:sol_log_': 3}))

    @unittest.skipUnless(os.environ.get('PUMP_OBJDUMP'), 'requires explicit SBF llvm-objdump')
    def test_actual_census_cli_reports_the_retained_cto_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / 'symbols.so'
            candidate.write_bytes(gzip.decompress(ARCHIVE.read_bytes()))
            output, markdown = root / 'census.json', root / 'census.md'
            reports = []
            for seed in ('0', '1'):
                result = subprocess.run([sys.executable, '-B', str(LANE / 'census.py'),
                    '--cand', str(candidate), '--only', '0x22a10,0x72810',
                    '--json', str(output), '--md', str(markdown)], capture_output=True, text=True,
                    env=dict(os.environ, PYTHONHASHSEED=seed))
                self.assertEqual(result.returncode, 0, result.stderr)
                reports.append((output.read_bytes(), markdown.read_bytes()))
            self.assertEqual(reports[0], reports[1], 'report ordering depends on hash seed')
            targets = {t['original']: t for t in json.loads(output.read_text())['targets']}
            cto = targets['0x22a10']['calls']
            self.assertEqual(cto['orig_syscalls'], {'symbol:abort': 1, 'symbol:sol_log_': 2})
            self.assertEqual(cto['our_syscalls'], {'symbol:sol_log_': 3})
            self.assertEqual([cto[k] for k in ('orig', 'ours', 'aligned')], [154, 178, 80])
            sweep = targets['0x72810']['calls']
            self.assertEqual(sweep['orig_syscalls'], sweep['our_syscalls'])
            self.assertEqual([sweep[k] for k in ('orig', 'ours', 'aligned')], [37, 36, 32])
            messages = [line for line in markdown.read_text().splitlines()
                        if line.startswith('syscall multiset differs:')]
            self.assertEqual(len(messages), 1)
            self.assertIn('symbol:abort', messages[0])


if __name__ == '__main__':
    unittest.main()
