"""Group cleanup after the command exits must not lose the trial's receipt."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import experiment_runner as runner  # noqa: E402


class ProcessGroupGoneTests(unittest.TestCase):
    def test_permission_error_from_a_finished_group_keeps_the_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / 'source').mkdir()
            (root / 'source/lib.rs').write_text('fixture')
            destination = root / 'trial'
            with patch.object(runner.os, 'killpg', side_effect=PermissionError(1, 'Operation not permitted')):
                try:
                    record = runner.run_trial(root / 'source', [sys.executable, '-c', 'pass'], destination)
                except PermissionError as error:
                    self.fail(f'finished trial left no receipt: {error}')
            self.assertEqual(record['status'], 'pass')
            self.assertEqual(json.loads((destination / 'latest.json').read_text())['status'], 'pass')


if __name__ == '__main__':
    unittest.main()
