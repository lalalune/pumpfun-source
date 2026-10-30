"""All nine retained ledgers, real old/new CLI reads and failed-record controls."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import read

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent


class SavedAmmRankingTests(unittest.TestCase):
    def invoke(self, script, *arguments, env=None):
        result = subprocess.run([sys.executable, '-I', '-B', '-X', 'utf8', str(script), *map(str, arguments)],
                                env=env, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_all_retained_ledgers_use_the_same_no_loss_policy_as_best_publication(self):
        folder = ROOT / 'scripts/amm_sell'
        ledgers = [folder / 'attempts/seed.jsonl', *sorted((folder / 'lanes').glob('*/attempts.jsonl'))]
        self.assertEqual(len(ledgers), 9)
        rank, _ = read.canonical_rank()
        totals = {'records': 0, 'builds': 0, 'old_eligible': 0, 'new_eligible': 0, 'omitted': 0}
        with tempfile.TemporaryDirectory(prefix='pump-amm-saved-rank-') as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.name.startswith('pump-amm-saved-rank-'))
            # Read-only baseline adaptation: remove the unused POSIX note-lock
            # import so actual old `best` can run on Windows; no function changes.
            original_source = (folder / 'attempts.py').read_text(encoding='utf-8')
            self.assertEqual(original_source.count('import fcntl\n'), 1)
            legacy = root / 'attempts.py'
            legacy.write_text(original_source.replace('import fcntl\n', ''), encoding='utf-8')
            for index, ledger in enumerate(ledgers):
                retained = ledger.read_bytes()
                records = [json.loads(line) for line in retained.decode('utf-8').split('\n') if line.strip()]
                builds = [row for row in records if row.get('schema') == 'amm-sell-attempt-v1']
                old_selected = [row for row in builds if (row.get('metrics') or {}).get('lost_windows_count') == 0]
                canonical = [row for row in builds if rank(row) is not None]
                canonical.sort(key=rank)
                swarm = root / str(index)
                swarm.mkdir()
                (swarm / 'ATTEMPTS.jsonl').write_bytes(retained)
                old = self.invoke(legacy, 'best', '1000', env=dict(os.environ, AMM_SELL_SWARM=str(swarm)))
                self.assertEqual(len(re.findall(r'(?m)^.* dist=.* lost=', old.stdout)), len(old_selected))
                fresh = self.invoke(PACKAGE / 'read.py', '--ledger', swarm / 'ATTEMPTS.jsonl', '--limit', '1000')
                result = json.loads(fresh.stdout)
                self.assertEqual([row['record']['attempt_id'] for row in result['best']],
                                 [row['attempt_id'] for row in canonical])
                self.assertEqual(result['ledger_sha256'], hashlib.sha256(retained).hexdigest())
                for item in result['best']:
                    self.assertEqual(item['normalized_loss_count'], 0)
                    self.assertEqual(item['raw_loss_count'], item['record']['metrics']['lost_windows_count'])
                self.assertEqual((swarm / 'ATTEMPTS.jsonl').read_bytes(), retained)
                self.assertEqual(ledger.read_bytes(), retained)
                totals['records'] += len(records)
                totals['builds'] += len(builds)
                totals['old_eligible'] += len(old_selected)
                totals['new_eligible'] += len(canonical)
                totals['omitted'] += sum(row['metrics']['lost_windows_count'] > 0 for row in canonical)
            self.assertEqual(totals, {'records': 353, 'builds': 306, 'old_eligible': 55,
                                      'new_eligible': 266, 'omitted': 211})

    def test_failed_and_incomplete_records_do_not_rank_from_leftover_metrics(self):
        source = ROOT / 'scripts/amm_sell/attempts/seed.jsonl'
        rows = [json.loads(line) for line in source.read_text(encoding='utf-8').split('\n') if line.strip()]
        original = next(row for row in rows if row.get('schema') == 'amm-sell-attempt-v1' and row.get('metrics'))
        failed = {**original, 'status': 'build_failed', 'attempt_id': 'failed-control'}
        incomplete = {**original, 'attempt_id': 'incomplete-control',
                      'metrics': {key: value for key, value in original['metrics'].items() if key != 'align_distance'}}
        with tempfile.TemporaryDirectory(prefix='pump-amm-saved-rank-') as temporary:
            path = Path(temporary) / 'ledger.jsonl'
            path.write_text('\n'.join(json.dumps(row) for row in [failed, incomplete, original]) + '\n', encoding='utf-8')
            result = read.read_best(path, 1000)
            self.assertEqual([row['record']['attempt_id'] for row in result['best']], [original['attempt_id']])
            self.assertEqual(result['counts']['failed_or_unscored'], 1)
            self.assertEqual(result['counts']['incomplete_metrics'], 1)


if __name__ == '__main__':
    unittest.main()
