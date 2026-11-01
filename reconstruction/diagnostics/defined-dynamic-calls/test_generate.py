"""Actual defined/undefined relocations, unchanged matching data and full CLI."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import generate

try:
    import resource
except ImportError:
    resource = None


def limit_file_size():
    resource.setrlimit(resource.RLIMIT_FSIZE, (64, 64))

ROOT = Path(__file__).resolve().parents[3]
EXPECTED = {
    'pump': (1748104, 1405624, 10591, 269, 144, 11005, '1679e63df634b44e02a7b909fe81bbfc20f1d7388ac33f5ca171a12f8e711ccf'),
    'pump_amm': (1117752, 976048, 7223, 173, 123, 7520, 'ab6eee08090aa222a526bd7e391323657fd9619bb4e7241262d4c1b06c5e5d04'),
    'mayhem': (668552, 537888, 4768, 133, 93, 4995, '3ef8c6f0b667bc0e6f586edc9099a02d315637d999894cec5a32245d0a74a8c3'),
}


class DynamicCallTests(unittest.TestCase):
    def run_cli(self, output, **kwargs):
        return subprocess.run([sys.executable, '-B', '-X', 'utf8', str(Path(generate.__file__)),
                               '--repo', str(ROOT), '--output', str(output)],
                              capture_output=True, text=True, encoding='utf-8', timeout=90, **kwargs)

    @unittest.skipUnless(resource is not None and os.name == 'posix', 'requires POSIX file-size limits')
    def test_failed_write_preserves_retry_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary).resolve()
            output = parent / 'packet'
            failed = self.run_cli(output, preexec_fn=limit_file_size)
            self.assertNotEqual(failed.returncode, 0)
            self.assertFalse(output.exists())
            self.assertEqual(list(parent.iterdir()), [])
            retried = self.run_cli(output)
            self.assertEqual(retried.returncode, 0, retried.stderr)
            manifest = json.loads((output / 'manifest.json').read_bytes())
            self.assertIn('dynamic-call-inputs.json', manifest)
            for name, digest in manifest.items():
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), digest)

    def test_dangling_output_link_does_not_create_its_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary).resolve()
            output, target = parent / 'packet', parent / 'untouched'
            try:
                output.symlink_to(target, target_is_directory=True)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f'symlinks unavailable: {error}')
            result = self.run_cli(output)
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(output.is_symlink())
            self.assertFalse(target.exists())

    def test_late_empty_destination_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary).resolve()
            output = parent / 'packet'
            created = []
            def observe(frame, event, arg):
                if (event == 'return' and frame.f_code.co_name == 'generate_roadmap'
                        and frame.f_code.co_filename == str(ROOT / 'scripts/reconstruction_roadmap.py')):
                    sys.setprofile(None)
                    if not output.exists():
                        output.mkdir()
                        created.append(True)
                return observe
            sys.setprofile(observe)
            try:
                with self.assertRaises(FileExistsError):
                    generate.generate(ROOT, output)
            finally:
                sys.setprofile(None)
            self.assertEqual(created, [True])
            self.assertEqual(list(output.iterdir()), [])
            self.assertEqual(list(parent.iterdir()), [output])

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
