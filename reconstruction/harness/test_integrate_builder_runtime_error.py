"""A RuntimeError from the builder must not discard the composition report."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import integrate  # noqa: E402


class BuilderRuntimeErrorReportTests(unittest.TestCase):
    def crate(self, path, body):
        (path / 'src').mkdir(parents=True)
        (path / 'Cargo.toml').write_text('[package]\nname="synthetic"\nversion="0.0.0"\n')
        (path / 'Cargo.lock').write_text('version = 3\n')
        (path / 'src/lib.rs').write_text(body)

    def test_link_receipt_failure_keeps_the_part_statuses(self):
        failure = RuntimeError('link receipt does not match the pinned link script')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            self.crate(root / 'crate', '// base\n')
            self.crate(root / 'part', '// part\n')
            baseline = root / 'pump-main/baseline/score.json'
            baseline.parent.mkdir(parents=True)
            baseline.write_text('{"windows": {}}')
            argv = ['integrate.py', '--name', 'trial', '--base-src', str(root / 'crate'),
                    '--part', f'one={root / "part"}']
            with patch.object(integrate, 'SC', root), patch.object(sys, 'argv', argv), \
                 patch.object(integrate, 'build_source', side_effect=failure), \
                 contextlib.redirect_stdout(io.StringIO()):
                try:
                    status = integrate.main()
                except RuntimeError as error:
                    self.fail(f'builder failure discarded the report: {error}')
            report = json.loads((root / 'integ/trial/report.json').read_text())
        self.assertEqual(status, 1)
        self.assertEqual([part['status'] for part in report['parts']], ['applied'])
        self.assertEqual(report['error'], str(failure))
        self.assertNotIn('score', report)


if __name__ == '__main__':
    unittest.main()
