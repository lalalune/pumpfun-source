import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import score  # noqa: E402


@unittest.skipUnless(os.name == 'posix', 'POSIX file modes')
class ScoreReportModeTests(unittest.TestCase):
    def published_mode(self, umask):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'report.json'
            previous = os.umask(umask)
            try:
                score.write_report(output, '{}\n')
            finally:
                os.umask(previous)
            self.assertEqual(output.read_text(encoding='utf-8'), '{}\n')
            self.assertEqual(list(Path(directory).glob('.score-*')), [])
            return stat.S_IMODE(output.stat().st_mode)

    def test_report_keeps_the_mode_a_plain_open_would_give(self):
        for umask in (0o022, 0o027, 0o077):
            with self.subTest(umask=oct(umask)):
                self.assertEqual(self.published_mode(umask), 0o666 & ~umask)


if __name__ == '__main__':
    unittest.main()
