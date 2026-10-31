import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

try:
    import minimize_experiment as reducer
except ModuleNotFoundError as error:
    if error.name != 'fcntl':
        raise
    reducer = None


@unittest.skipIf(reducer is None, 'experiment runner imports POSIX fcntl')
class MinimizeGitContextTests(unittest.TestCase):
    def exercise(self, redirect):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, outside = root / 'source', root / 'unrelated'
            source.mkdir(); outside.mkdir()
            for folder in (source, outside):
                (folder / 'value.txt').write_bytes(b'old\n')
            clean = {k: v for k, v in os.environ.items() if not k.upper().startswith('GIT_')}
            before = {p.relative_to(outside).as_posix(): p.read_bytes()
                      for p in outside.rglob('*') if p.is_file()}
            delta = root / 'change.patch'
            delta.write_bytes(b'diff --git a/value.txt b/value.txt\n--- a/value.txt\n+++ b/value.txt\n@@ -1 +1 @@\n-old\n+new\n')
            patches, oracle, output = root / 'patches.json', root / 'oracle.json', root / 'output'
            patches.write_text(json.dumps([str(delta)]), encoding='utf-8')
            oracle.write_text(json.dumps({'command': ['unused']}), encoding='utf-8')
            environment = dict(clean)
            if redirect:
                environment.update(GIT_DIR=str(outside / '.git'), GIT_WORK_TREE=str(outside))
            calls = []
            def evaluate(stage, *args):
                value = (stage / 'value.txt').read_text(encoding='utf-8')
                calls.append(value)
                return {'status': 'pass' if value == 'new\n' else 'fail'}
            argv = ['minimize_experiment.py', '--source', str(source), '--patches', str(patches),
                    '--oracle', str(oracle), '--out', str(output)]
            with patch.dict(os.environ, environment, clear=True), patch.object(sys, 'argv', argv), \
                    patch.object(reducer, 'run_trial', side_effect=evaluate), contextlib.redirect_stdout(io.StringIO()):
                result = reducer.main()
            self.assertEqual(result, 0, (output / 'minimized.json').read_text(encoding='utf-8'))
            self.assertEqual(calls, ['new\n', 'old\n'])
            saved = json.loads((output / 'minimized.json').read_text(encoding='utf-8'))
            self.assertEqual(saved['selected'], [0])
            self.assertTrue(saved['one_minimal'])
            self.assertEqual((source / 'value.txt').read_bytes(), b'old\n')
            self.assertEqual({p.relative_to(outside).as_posix(): p.read_bytes()
                              for p in outside.rglob('*') if p.is_file()}, before)

    def test_inherited_repository_routing_cannot_initialize_an_unrelated_tree(self):
        self.exercise(True)

    def test_ordinary_patch_minimization_still_works(self):
        self.exercise(False)


if __name__ == '__main__':
    unittest.main()
