"""Attached linker scripts must not bypass the admitted text-order script."""
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pump_text_layout as layout


class AttachedLinkerScriptTests(unittest.TestCase):
    def test_separate_script_argument_is_admitted(self):
        self.assertEqual(layout.declared_inputs(['ld', '-T', 'default.ld', '--script', 'other.ld']), {})

    def test_attached_script_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'attached linker script'):
            layout.declared_inputs(['ld', '--script', 'default.ld', '-Tevil.ld'])

    def test_prepare_link_rejects_attached_script(self):
        default = (ROOT / 'scripts/pump_text_layout_default.ld').read_text()
        head, tail = default.split(layout.RULE)
        admitted = head + '  .text : {\n' + '\n    *(.text*)\n  } :text' + tail
        with tempfile.TemporaryDirectory() as temporary:
            script = Path(temporary) / 'ordered.ld'
            script.write_text(admitted)
            with self.assertRaisesRegex(AssertionError, 'attached linker script'):
                layout.prepare_link(
                    ['ld', '--script', str(ROOT / 'scripts/pump_text_layout_default.ld'), '-Tevil.ld'],
                    {
                        'PUMP_TEXT_RECORD_DIR': str(Path(temporary) / 'record'),
                        'PUMP_TEXT_SCRIPT': str(script),
                    },
                )


if __name__ == '__main__':
    unittest.main(verbosity=2)
