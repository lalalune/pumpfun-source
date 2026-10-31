import hashlib
from pathlib import Path
import tempfile
import unittest
import link_order


class ScriptLineEndings(unittest.TestCase):
    default = link_order.DEFAULT.read_text(encoding='utf-8')

    def ordered(self):
        return self.default.replace('  .text : { *(.text*) } :text',
            '  .text : {\n    *(".text.example")\n    *(.text*)\n  } :text')

    def test_lf_and_crlf_scripts_have_the_same_admission(self):
        expected = link_order.check_script(self.ordered(), self.default)
        for text in (self.ordered(), self.ordered().replace('\n', '\r\n')):
            for default in (self.default, self.default.replace('\n', '\r\n')):
                with self.subTest(crlf='\r' in text, default_crlf='\r' in default):
                    self.assertEqual(link_order.check_script(text, default), expected)
        bad = self.ordered().replace('    *(".text.example")', '    BYTE(0)')
        with self.assertRaises(ValueError): link_order.check_script(bad.replace('\n', '\r\n'))

    def test_configure_preserves_raw_crlf_script_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'link').mkdir()
            (root / 'Cargo.toml').write_bytes(b'[package]\nname="pump"\nversion="0.1.0"\n')
            raw = self.ordered().replace('\n', '\r\n').encode()
            (root / 'link/ordered.ld').write_bytes(raw)
            lld = root / 'rust/lib/rustlib/host/bin/rust-lld'
            lld.parent.mkdir(parents=True); lld.write_bytes(b'not executed')
            env, record = link_order.configure(root, root / 'rust/bin/rustc', root / 'receipt.json')
            self.assertEqual(record['script_sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual((root / 'link/ordered.ld').read_bytes(), raw)

    def test_linker_default_comparison_accepts_crlf_without_rewriting(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pinned, original = root / 'ordered.ld', root / 'default.ld'
            raw = self.ordered().replace('\n', '\r\n').encode()
            default = self.default.replace('\n', '\r\n').encode()
            pinned.write_bytes(raw); original.write_bytes(default)
            env = {'PUMP_LINK_SCRIPT': str(pinned), 'PUMP_LINK_SCRIPT_SHA256': hashlib.sha256(raw).hexdigest()}
            self.assertEqual(link_order.lld_args(['-T', str(original)], env, default_bytes=default), ['-T', str(pinned)])
            self.assertEqual(pinned.read_bytes(), raw)
            self.assertEqual(original.read_bytes(), default)


if __name__ == '__main__': unittest.main()
