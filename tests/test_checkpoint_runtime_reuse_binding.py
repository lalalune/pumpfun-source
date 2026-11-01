"""A checkpoint may not reuse runtime cases for an image it does not publish.

``runtime-reuse.json`` carries the historical admin-CTO cases forward with
``"fresh_VM_executions": 0`` on one condition: the fresh stripped image must
equal ``candidate_sha256_required_for_reuse``. The file states that condition in
prose ("Parent must verify ...") and nothing in the repository performed it, so
a checkpoint could publish one image and still cite the cases captured against
another.

``reconstruction/pump-main/checkpoints/verify_reuse.py`` reads the checkpoint's
own build, summary, historical receipt bytes and historical summary, and refuses
when they do not all name the same image.
"""
import gzip
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / 'reconstruction/pump-main/checkpoints/verify_reuse.py'
CURRENT = 'completion-pass106-20261031'
HISTORICAL = 'completion-pass104-20261031'


def run(root):
    return subprocess.run([sys.executable, '-I', '-B', str(VERIFIER), '--repo-root', str(root)],
                          text=True, capture_output=True, timeout=300)


def copy_checkpoints(directory):
    """Copy the reusing checkpoint and the one it cites into a temporary tree."""
    root = Path(directory)
    target = root / 'reconstruction/pump-main/checkpoints'
    for name in (CURRENT, HISTORICAL):
        shutil.copytree(ROOT / 'reconstruction/pump-main/checkpoints' / name, target / name)
    return root, target


def rewrite(path, update):
    data = json.loads(path.read_text())
    update(data)
    path.write_text(json.dumps(data))


class RuntimeReuseBindingTests(unittest.TestCase):
    def test_empty_or_missing_discovery_never_reports_success(self):
        with tempfile.TemporaryDirectory(prefix='reuse-empty-') as temporary:
            empty = Path(temporary)
            for root in (empty, empty / 'missing'):
                for flag in (None, '-O', '-OO'):
                    with self.subTest(root=root, optimization=flag):
                        command = [sys.executable, *([flag] if flag else []), '-B',
                                   str(VERIFIER), '--repo-root', str(root)]
                        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                        self.assertIn('no checkpoint packets found', result.stderr)
                        self.assertNotIn('PASS:', result.stdout)

    def test_pristine_checkpoints_bind_their_reuse(self):
        completed = run(ROOT)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertRegex(completed.stdout, r'PASS: [1-9]\d* of [1-9]\d* checkpoints reuse')

    def test_optimized_interpreters_preserve_the_reuse_gate(self):
        for flag in ('-O', '-OO'):
            with self.subTest(flag=flag):
                completed = subprocess.run(
                    [sys.executable, flag, '-B', str(VERIFIER), '--repo-root', str(ROOT)],
                    text=True, capture_output=True, timeout=300)
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                self.assertIn('checkpoints reuse a runtime receipt', completed.stdout)

    def test_the_receipt_must_belong_to_its_named_historical_checkpoint(self):
        with tempfile.TemporaryDirectory(prefix='reuse-location-') as directory:
            root, checkpoints = copy_checkpoints(directory)
            copied = checkpoints / 'another-checkpoint'
            shutil.copytree(checkpoints / HISTORICAL, copied)
            rewrite(checkpoints / CURRENT / 'runtime-reuse.json',
                    lambda data: data.update(historical_checkpoint='another-checkpoint'))
            tampered = run(root)
            self.assertNotEqual(tampered.returncode, 0, tampered.stdout)
            self.assertIn('not in its named historical checkpoint', tampered.stderr)

    def test_the_historical_transcript_must_name_the_required_image(self):
        import hashlib
        with tempfile.TemporaryDirectory(prefix='reuse-transcript-') as directory:
            root, checkpoints = copy_checkpoints(directory)
            receipt = checkpoints / HISTORICAL / 'admin-runtime.json.gz'
            data = json.loads(gzip.decompress(receipt.read_bytes()))
            data['candidate_sha256'] = '00' * 32
            raw = (json.dumps(data) + '\n').encode()
            compressed = gzip.compress(raw, mtime=0)
            receipt.write_bytes(compressed)
            rewrite(checkpoints / CURRENT / 'runtime-reuse.json',
                    lambda data: data.update(
                        historical_compressed_sha256=hashlib.sha256(compressed).hexdigest(),
                        historical_uncompressed_sha256=hashlib.sha256(raw).hexdigest()))
            tampered = run(root)
            self.assertNotEqual(tampered.returncode, 0, tampered.stdout)
            self.assertIn('historical receipt candidate', tampered.stderr)

    def test_a_historical_checkpoint_path_cannot_escape_the_checkpoint_tree(self):
        with tempfile.TemporaryDirectory(prefix='reuse-parent-') as directory:
            root, checkpoints = copy_checkpoints(directory)
            rewrite(checkpoints / CURRENT / 'runtime-reuse.json',
                    lambda data: data.update(historical_checkpoint='../elsewhere'))
            tampered = run(root)
            self.assertNotEqual(tampered.returncode, 0, tampered.stdout)
            self.assertIn('must be a sibling name', tampered.stderr)

    def test_a_build_that_publishes_another_image_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='reuse-build-') as directory:
            root, checkpoints = copy_checkpoints(directory)
            rewrite(checkpoints / CURRENT / 'build.json',
                    lambda data: data.update(candidate_sha256='00' * 32))
            tampered = run(root)
            self.assertNotEqual(tampered.returncode, 0, tampered.stdout)
            self.assertIn('build candidate', tampered.stderr)

    def test_a_historical_receipt_with_another_content_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='reuse-receipt-') as directory:
            root, checkpoints = copy_checkpoints(directory)
            receipt = checkpoints / HISTORICAL / 'admin-runtime.json.gz'
            receipt.write_bytes(gzip.compress(b'{"cases": []}', mtime=0))
            tampered = run(root)
            self.assertNotEqual(tampered.returncode, 0, tampered.stdout)
            self.assertIn('historical receipt', tampered.stderr)

    def test_a_historical_checkpoint_that_publishes_another_image_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='reuse-history-') as directory:
            root, checkpoints = copy_checkpoints(directory)
            rewrite(checkpoints / HISTORICAL / 'summary.json',
                    lambda data: data.update(stripped_sha256='11' * 32))
            tampered = run(root)
            self.assertNotEqual(tampered.returncode, 0, tampered.stdout)
            self.assertIn('historical ' + HISTORICAL, tampered.stderr)


if __name__ == '__main__':
    unittest.main()
