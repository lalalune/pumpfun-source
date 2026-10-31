"""rust-lld reads -script like --script, so the hook must not let either form through."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import link_order as L  # noqa: E402


class SingleDashScriptTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.default = root / 'rustc-sbf-linkfile.ld'
        self.default.write_text(L.DEFAULT.read_text())
        self.other = root / 'other.ld'
        self.other.write_text('SECTIONS { .text : { *(.text*) BYTE(0) } }\n')
        pinned = root / 'ordered.ld'
        pinned.write_text(L.DEFAULT.read_text())
        self.env = {'PUMP_LINK_SCRIPT': str(pinned), 'PUMP_LINK_SCRIPT_SHA256': L.sha(pinned)}
        self.linked = ['-flavor', 'gnu', 'a.o', '--script', str(self.default), '-o', 'x.so']

    def test_additional_unchecked_script_is_refused(self):
        for extra in ([f'-script={self.other}'], ['-script', str(self.other)]):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                L.lld_args(self.linked + extra, self.env)

    def test_only_single_dash_default_script_is_replaced(self):
        try:
            out = L.lld_args(['a.o', '-script', str(self.default)], self.env)
        except ValueError as error:
            self.fail(f'single-dash default script was not recognized: {error}')
        self.assertEqual(out, ['a.o', '-script', self.env['PUMP_LINK_SCRIPT']])


if __name__ == '__main__':
    unittest.main()
