"""Actual defined/undefined relocations, unchanged matching data and full CLI."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import generate

ROOT = Path(__file__).resolve().parents[3]
EXPECTED = {
    'pump': (1748104, 1405624, 10591, 269, 144, 11005, '1679e63df634b44e02a7b909fe81bbfc20f1d7388ac33f5ca171a12f8e711ccf'),
    'pump_amm': (1117752, 976048, 7223, 173, 123, 7520, 'ab6eee08090aa222a526bd7e391323657fd9619bb4e7241262d4c1b06c5e5d04'),
    'mayhem': (668552, 537888, 4768, 133, 93, 4995, '3ef8c6f0b667bc0e6f586edc9099a02d315637d999894cec5a32245d0a74a8c3'),
}


class DynamicCallTests(unittest.TestCase):
    def test_actual_defined_hooks_are_internal_graph_edges(self):
        roadmap, reader, proof, _ = generate.load_sources(ROOT)
        fixed_reader = generate.resolved_reader(reader)
        classify = generate.classifier(roadmap)
        for name, (at, target, static, external, indirect, calls, digest) in EXPECTED.items():
            path = ROOT / f'evidence/original/{name}/deployed.so'
            old, new = reader.Elf(path), fixed_reader(path)
            self.assertNotIn(at, old.calls, name)
            self.assertEqual(proof.corrected_classify(roadmap)(old.b, at, old), 'syscall_custom_panic')
            self.assertEqual(new.defined_calls, {at: target}, name)
            self.assertEqual(new.calls[at], target)
            self.assertEqual(classify(new.b, at, new), 'call_internal')
            self.assertEqual(len(new.calls), static + 1)
            self.assertEqual(len(new.external_symbols), external)
            self.assertTrue(set(new.external_symbols).isdisjoint(new.calls))
            self.assertEqual(new.entries, old.entries)
            self.assertEqual(new.normalized, old.normalized)
            self.assertEqual(hashlib.sha256(new.normalized).hexdigest(), digest)
            self.assertEqual(new.pattern(new.lo, new.hi - new.lo), old.pattern(old.lo, old.hi - old.lo))
            self.assertIn({'offset': at - new.lo, 'target': target}, new.callsites(new.lo, new.hi - new.lo))
            index = {entry: {} for entry in new.entries}
            forward, reverse = roadmap.build_call_tree(new, new.entries, index)
            caller = max(entry for entry in new.entries if entry <= at)
            self.assertIn(target, forward[caller])
            self.assertIn(caller, reverse[target])

    def test_complete_cli_census_and_packet_verifier(self):
        with tempfile.TemporaryDirectory(prefix='pump-defined-calls-') as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.name.startswith('pump-defined-calls-'))
            output = root / 'packet'
            result = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(Path(generate.__file__)),
                                     '--output', str(output)], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for name, (_, _, _, external, indirect, calls, _) in EXPECTED.items():
                data = json.loads((output / f'{name}-details.json').read_text(encoding='utf-8'))
                windows = data['window_details']
                self.assertEqual(sum(w['calls'] for w in windows), calls, name)
                self.assertEqual(sum(sum(w['syscalls'].values()) for w in windows), external, name)
                self.assertFalse(any('syscall_custom_panic' in w['syscalls'] for w in windows), name)
                self.assertEqual(data['deployed_sha256'], hashlib.sha256(
                    (ROOT / f'evidence/original/{name}/deployed.so').read_bytes()).hexdigest())
            verified = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(output / 'verify.py')],
                                      capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)


if __name__ == '__main__':
    unittest.main()
