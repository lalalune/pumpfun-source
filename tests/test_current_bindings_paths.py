"""Path-boundary regressions for the current binding verifier."""
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_current_bindings


class CurrentBindingsPathTests(unittest.TestCase):
    def test_verify_maps_rejects_symlinked_ancestor(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root / "outside"
            outside.mkdir()
            data = b"tracked bytes\n"
            (outside / "input.py").write_bytes(data)
            os.symlink(outside, root / "alias", target_is_directory=True)
            tracked = {"alias/input.py"}
            groups = {"source": {"alias/input.py": hashlib.sha256(data).hexdigest()}}

            with self.assertRaisesRegex(AssertionError, "Symlink ancestry"):
                verify_current_bindings.verify_maps(root, groups, tracked)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs need POSIX")
    def test_fifo_input_is_rejected_without_blocking(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            os.mkfifo(root / "input.py")
            script = """
import importlib.util
from pathlib import Path, PureWindowsPath
import sys

spec = importlib.util.spec_from_file_location("verify_current_bindings", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
try:
    module.verify_maps(Path(sys.argv[2]),
                       {"source": {"input.py": "0" * 64}},
                       {"input.py"})
except AssertionError as error:
    if "Nonregular input" not in str(error):
        raise
else:
    raise SystemExit("a FIFO was accepted")
"""
            module = Path(__file__).resolve().parents[1] / "scripts/verify_current_bindings.py"
            try:
                result = subprocess.run(
                    [sys.executable, "-B", "-c", script, str(module), str(root)],
                    capture_output=True, text=True, timeout=3,
                )
            except subprocess.TimeoutExpired:
                self.fail("read_regular blocked on a FIFO")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_candidate_key_uses_the_tracked_spelling(self):
        # The candidate map key used str(relative_to(ROOT)), which is
        # backslash-spelled on Windows and never matched the forward-slash
        # set built from `git ls-files`, so every Windows run raised
        # ('Unpublished input', 'candidate', ...) for a tracked file.
        package = verify_current_bindings.ROOT / "repro/pump/tokenkeg-two-curve-fortyeight"
        key = verify_current_bindings.tracked_key(package / "candidate.so")
        self.assertEqual(key, "repro/pump/tokenkeg-two-curve-fortyeight/candidate.so")
        self.assertNotIn("\\", key)
        # The admission accepts exactly this spelling against a tracked set.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = root / key
            payload.parent.mkdir(parents=True)
            payload.write_bytes(b"payload")
            import hashlib as _hashlib
            real_digest = _hashlib.sha256(b"payload").hexdigest()
            checked, _ = verify_current_bindings.verify_maps(
                root, {"candidate": {key: real_digest}}, {key})
            self.assertEqual(checked, 1)


    def test_windows_candidate_key_uses_git_separators(self):
        root = PureWindowsPath('C:/repository')
        with patch.object(verify_current_bindings, 'ROOT', root):
            key = verify_current_bindings.tracked_key(root / 'repro/package/candidate.so')
        self.assertEqual(key, 'repro/package/candidate.so')

    def test_actual_group_builder_uses_the_tracked_candidate_key(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / 'repro/package'; package.mkdir(parents=True)
            source = {str(i): 'source' for i in range(36)}
            documents = {
                'source-harness-sha256.json': {'source': source, 'canonical_harness': {'a':'a','b':'b'},
                    'static_and_saved_verifiers': {}, 'owned_documentation': {}},
                'source-sha256.json': source,
                'scratch-inputs-before.json': {'harness_sha256': {str(i):'h' for i in range(94)},
                    'repository_fixture_snapshot_sha256': {str(i):'r' for i in range(28)}},
                'build-helper-sha256.json': {'a':'a','b':'b','c':'c'},
                'manifest-sha256.json': {'candidate.so': {'sha256':'candidate-digest'}},
            }
            for name, document in documents.items():
                (package / name).write_text(json.dumps(document))
            with patch.object(verify_current_bindings, 'ROOT', root), \
                    patch.object(verify_current_bindings, 'tracked_key', wraps=verify_current_bindings.tracked_key) as key:
                groups = verify_current_bindings.current_pump_groups(package)
            key.assert_called_once_with(package / 'candidate.so')
            self.assertEqual(groups['candidate'], {'repro/package/candidate.so':'candidate-digest'})


if __name__ == "__main__":
    unittest.main(verbosity=2)
