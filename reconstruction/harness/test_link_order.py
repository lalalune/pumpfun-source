"""Pinned link-order hooks admit only input-section reordering; no compiler, linker or SDK is run."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import link_order as L

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = L.DEFAULT.read_text()
TEXT = '  .text : { *(.text*) } :text'


def ordered(lines, name='.text', seg='text'):
    body = f'  {name} : {{\n' + ''.join(l + '\n' for l in lines) + f'    *({name}*)\n  }} :{seg}'
    return DEFAULT.replace(f'  {name} : {{ *({name}*) }} :{seg}', body)


class ScriptTests(unittest.TestCase):
    def test_default_and_tracked_script_are_admitted(self):
        self.assertEqual(L.check_script(DEFAULT), {'.text': 0, '.rodata': 0, '.data.rel.ro': 0})
        tracked = ROOT / 'programs/pump' / L.SCRIPT
        counts = L.check_script(tracked.read_text())
        self.assertGreater(counts['.text'], 0)

    def test_default_matches_sdk_copy_used_by_text_layout_helper(self):
        self.assertEqual(DEFAULT, (ROOT / 'scripts/pump_text_layout_default.ld').read_text())

    def test_selectors_and_globs(self):
        text = ordered(['    *libcore-*.rlib:*(".text._ZN4core3fmt5write17h0123456789abcdefE")',
                        '    *pump_recovered.pump_recovered.*-cgu.0.rcgu.o(.text*)',
                        '    *(".text.__rust_alloc_error_handler")'])
        self.assertEqual(L.check_script(text)['.text'], 3)
        ro = ordered(['    *(".rodata..L__unnamed_1")'], '.rodata', 'rodata')
        self.assertEqual(L.check_script(ro)['.rodata'], 1)

    def test_rejects_anything_but_reordering(self):
        for bad in ['    . = ALIGN(16);', '    BYTE(0)', '    FILL(0x00)', '    pad = .;',
                    '    *(".text.a") *(".text.b")', '    KEEP(*(".text.a"))', '    *(".rodata.x")',
                    '    *(".text.a" )', '    *libx.rlib:*(.data*)']:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                L.check_script(ordered([bad]))
        with self.assertRaises(ValueError):
            L.check_script(ordered(['    *(".text.a")', '    *(".text.a")']))
        with self.assertRaises(ValueError):
            L.check_script(DEFAULT.replace('. = SIZEOF_HEADERS;', '. = SIZEOF_HEADERS + 8;'))
        with self.assertRaises(ValueError):
            L.check_script(DEFAULT + '\nASSERT(1, "x")\n')
        with self.assertRaises(ValueError):  # catch-all must close the block
            L.check_script(DEFAULT.replace(TEXT, '  .text : {\n    *(".text.a")\n  } :text'))


class HookTests(unittest.TestCase):
    def env(self, root):
        script = root / 'ordered.ld'
        script.write_text(ordered(['    *(".text.a")']))
        return {'PUMP_LINK_ROOT_CRATE': 'pump_recovered', 'PUMP_LINK_NEXT_WRAPPER': '/next.py',
                'PUMP_LINK_SCRIPT': str(script), 'PUMP_LINK_SCRIPT_SHA256': L.sha(script)}

    def test_rustc_hook_only_for_root_cdylib(self):
        env = {'PUMP_LINK_ROOT_CRATE': 'pump_recovered', 'PUMP_LINK_NEXT_WRAPPER': '/next.py'}
        root = L.rustc_args(['w', 'rustc', '--crate-name', 'pump_recovered', '--crate-type', 'cdylib',
                             '--crate-type', 'lib', 'src/lib.rs'], env)
        self.assertEqual(root[:3], [sys.executable, '/next.py', 'rustc'])
        self.assertEqual(root[-2:], ['-C', 'linker=' + str(L.H / 'pump_link_lld.py')])
        for args in (['--crate-name', 'anchor_lang', '--crate-type', 'lib'],
                     ['--crate-name', 'pump_recovered', '--crate-type', 'lib'], ['-vV']):
            with self.subTest(args=args):
                self.assertEqual(L.rustc_args(['w', 'rustc', *args], env)[3:], args)

    def test_linker_swaps_exactly_the_default_script(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); env = self.env(root)
            target = root / 'rustc-sbf-linkfile.ld'; target.write_text(DEFAULT)
            args = ['-flavor', 'gnu', 'a.o', '--script', str(target), '-o', 'x.so', '--gc-sections']
            out = L.lld_args(args, env)
            self.assertEqual(out, ['-flavor', 'gnu', 'a.o', '--script', env['PUMP_LINK_SCRIPT'], '-o', 'x.so', '--gc-sections'])
            self.assertEqual(L.lld_args(args, dict(env, PUMP_LINK_MAP='/m'))[-1], '-Map=/m')
            with self.assertRaises(ValueError):
                L.lld_args(['a.o'], env)
            with self.assertRaises(ValueError):
                L.lld_args(args + ['-T', str(target)], env)
            other = root / 'other.ld'; other.write_text(DEFAULT + '\n')
            with self.assertRaises(ValueError):
                L.lld_args(['--script', str(other)], env)
            with self.assertRaises(ValueError):
                L.lld_args(['--script=' + str(target)], env)
            # lld expands @FILE before option parsing, hiding additional inputs and options.
            for response in ('@opts.rsp', '@'):
                with self.subTest(response=response), self.assertRaisesRegex(
                        ValueError, 'response-file linker input'):
                    L.lld_args(args + [response], env)
            Path(env['PUMP_LINK_SCRIPT']).write_text(DEFAULT)
            with self.assertRaises(ValueError):  # changed after configuration
                L.lld_args(args, env)

    def test_configure_reports_pins(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            crate = root / 'crate'; (crate / 'link').mkdir(parents=True)
            (crate / 'Cargo.toml').write_text('[package]\nname = "pump-recovered"\nversion = "0.1.0"\n')
            self.assertEqual(L.configure(crate, root / 'rust/bin/rustc', root / 'r.json'), ({}, None))
            (crate / L.SCRIPT).write_text(ordered(['    *(".text.a")']))
            lld = root / 'rust/lib/rustlib/host/bin/rust-lld'; lld.parent.mkdir(parents=True); lld.write_bytes(b'lld')
            env, record = L.configure(crate, root / 'rust/bin/rustc', root / 'r.json')
            self.assertEqual(env['PUMP_LINK_ROOT_CRATE'], 'pump_recovered')
            self.assertEqual(env['PUMP_LINK_LLD'], str(lld))
            self.assertEqual(record['selectors']['.text'], 1)
            self.assertEqual(record['lld_sha256'], L.sha(lld))
            json.dumps(record)


if __name__ == '__main__':
    unittest.main()
