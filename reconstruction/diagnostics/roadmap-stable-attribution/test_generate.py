"""Real full-CLI attribution and packet reproducibility regression."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent


class AttributionTests(unittest.TestCase):
    def run_python(self, *args, env=None):
        result = subprocess.run([sys.executable, '-B', '-X', 'utf8', *map(str, args)],
                                cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_actual_context_has_unique_minimum_distances_and_stable_packets(self):
        with tempfile.TemporaryDirectory(prefix='pump-stable-attribution-') as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.name.startswith('pump-stable-attribution-'))
            before = root / 'before'
            self.run_python(ROOT / 'scripts/reconstruction_roadmap.py', '--output', before)
            packets = []
            for seed in ['1', '2']:
                output = root / f'after-{seed}'
                self.run_python(PACKAGE / 'generate.py', '--output', output,
                                env=dict(os.environ, PYTHONHASHSEED=seed))
                packets.append(output)
                for name, address in [('pump', '0x156fe8'), ('pump_amm', '0xee1e0'), ('mayhem', '0x83190')]:
                    old = json.loads((before / f'{name}-details.json').read_text(encoding='utf-8'))
                    data = json.loads((output / f'{name}-details.json').read_text(encoding='utf-8'))
                    old_known = next(w for w in old['window_details'] if w['address'] == address)
                    self.assertEqual([c for c in old_known['likely_callers'] if c[0] == 'entrypoint'],
                                     [['entrypoint', 2], ['entrypoint', 3]])
                    for old_window, window in zip(old['window_details'], data['window_details']):
                        for key in ['likely_callers', 'likely_callees']:
                            expected = {}
                            for label, distance in old_window[key]:
                                expected[label] = min(distance, expected.get(label, distance))
                            self.assertEqual(window[key], [list(item) for item in sorted(
                                expected.items(), key=lambda item: (item[1], item[0]))])
                            self.assertEqual(len(window[key]), len({c[0] for c in window[key]}))
                        for key in old_window.keys() - {'likely_callers', 'likely_callees'}:
                            self.assertEqual(old_window[key], window[key], (name, key))
                self.run_python(output / 'verify.py')
            files = sorted(p.name for p in packets[0].iterdir() if p.is_file())
            self.assertEqual(files, sorted(p.name for p in packets[1].iterdir() if p.is_file()))
            for name in files:
                self.assertEqual((packets[0] / name).read_bytes(), (packets[1] / name).read_bytes(), name)


if __name__ == '__main__':
    unittest.main()
