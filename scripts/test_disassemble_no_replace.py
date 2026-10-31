"""Real native disassembly must not replace a concurrently created directory."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def probe():
    cc, objdump = shutil.which('cc'), shutil.which('objdump')
    if not sys.platform.startswith('linux') or not cc or not objdump:
        raise unittest.SkipTest('native Linux cc and objdump required')
    results = {}
    with tempfile.TemporaryDirectory(prefix='disassemble-race-') as temporary:
        root = Path(temporary)
        scripts = root / 'repo/scripts'
        scripts.mkdir(parents=True)
        for name in ('disassemble.py', 'analyze.py', 'deep_disassembly.py', 'window_elf_reader.py'):
            shutil.copyfile(ROOT / 'scripts' / name, scripts / name)
        capture = root / 'repo/evidence/original/pump/deployed.so'
        capture.parent.mkdir(parents=True)
        source = root / 'fixture.c'
        source.write_text('int proof_value(void) { return 42; }\nint main(void) { return proof_value(); }\n')
        subprocess.run([cc, '-O0', str(source), '-o', str(capture)], check=True, capture_output=True)
        launcher = root / 'objdump-forwarder'
        launcher.write_text(
            '#!' + sys.executable + '\nimport json,os,pathlib,sys\n'
            'if "-d" in sys.argv and os.environ.get("DISASSEMBLE_RACE"):\n'
            ' p=pathlib.Path(os.environ["DISASSEMBLE_RACE"]);p.mkdir(mode=0o711)\n'
            ' pathlib.Path(os.environ["DISASSEMBLE_MARKER"]).write_text(str(p.stat().st_ino))\n'
            ' if os.environ.get("DISASSEMBLE_NONEMPTY"): (p/"owned.txt").write_text("retained")\n'
            'os.execv(' + repr(objdump) + ',[' + repr(objdump) + ',*sys.argv[1:]])\n')
        launcher.chmod(0o755)
        for kind in ('absent', 'empty', 'nonempty'):
            output, marker = root / kind, root / (kind + '.inode')
            environment = dict(os.environ)
            for key in ('DISASSEMBLE_RACE', 'DISASSEMBLE_MARKER', 'DISASSEMBLE_NONEMPTY'):
                environment.pop(key, None)
            if kind != 'absent':
                environment.update(DISASSEMBLE_RACE=str(output), DISASSEMBLE_MARKER=str(marker))
            if kind == 'nonempty':
                environment['DISASSEMBLE_NONEMPTY'] = '1'
            run = subprocess.run([sys.executable, '-B', str(scripts / 'disassemble.py'),
                                  '--objdump', str(launcher), '--output', str(output)],
                                 env=environment, capture_output=True, text=True)
            result = {'returncode': run.returncode,
                      'stderr': run.stderr.replace(str(root), '<proof-root>'),
                      'children': sorted(path.name for path in output.iterdir()),
                      'input_sha256': hashlib.sha256(capture.read_bytes()).hexdigest()}
            if marker.exists():
                result['directory_preserved'] = output.stat().st_ino == int(marker.read_text())
            if (output / 'pump.asm').exists():
                assembly = (output / 'pump.asm').read_bytes()
                manifest = json.loads((output / 'manifest.json').read_text())
                result['real_symbol_disassembled'] = b'<proof_value>:' in assembly
                result['manifest_bound'] = (
                    manifest['outputs']['pump']['input_sha256'] == result['input_sha256']
                    and manifest['outputs']['pump']['output_sha256'] == hashlib.sha256(assembly).hexdigest())
            if (output / 'owned.txt').exists():
                result['owned_bytes'] = (output / 'owned.txt').read_text()
            result['staging_leftovers'] = [path.name for path in root.glob('.' + kind + '.*')]
            results[kind] = result
    return results


class NoReplaceTests(unittest.TestCase):
    def test_real_disassembly_preserves_concurrent_directories(self):
        results = probe()
        clean = results['absent']
        self.assertEqual(clean['returncode'], 0, clean['stderr'])
        self.assertTrue(clean['real_symbol_disassembled'])
        self.assertTrue(clean['manifest_bound'])
        for kind in ('empty', 'nonempty'):
            with self.subTest(kind=kind):
                row = results[kind]
                self.assertNotEqual(row['returncode'], 0, row)
                self.assertTrue(row['directory_preserved'], row)
                self.assertEqual(row['children'], [] if kind == 'empty' else ['owned.txt'])
                self.assertEqual(row['staging_leftovers'], [])
        self.assertEqual(results['nonempty']['owned_bytes'], 'retained')


if __name__ == '__main__':
    if sys.argv[1:] == ['--probe']:
        print(json.dumps(probe(), indent=2))
    else:
        unittest.main()
