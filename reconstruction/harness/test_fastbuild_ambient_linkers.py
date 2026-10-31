"""Exercise fastbuild's real staging and compiler environment with host Cargo.

The dependency-free fixture is a host cdylib, not a reconstructed SBF program.
Stop after the actual compiler returns: host library names differ from SBF's
publication names. No compiler result or generated executable is fabricated.
"""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import fastbuild


class CompilerObserved(Exception):
    pass


def native_probe():
    cargo, rustc = (shutil.which(name) for name in ('cargo', 'rustc'))
    if not cargo or not rustc or not shutil.which('rsync'):
        raise unittest.SkipTest('real host Cargo, rustc and rsync required')
    version = subprocess.check_output([rustc, '-vV'], text=True)
    host = next(line.removeprefix('host: ') for line in version.splitlines()
                if line.startswith('host: '))
    if not host.endswith('linux-gnu'):
        raise unittest.SkipTest('native ELF cdylib probe requires a Linux GNU host')
    variable = 'CARGO_TARGET_' + host.upper().replace('-', '_') + '_LINKER'
    results = {'rustc': version, 'cargo': subprocess.check_output([cargo, '-V'], text=True),
               'linker_variable': variable, 'cases': {}}
    with tempfile.TemporaryDirectory(prefix='fastbuild-linker-proof-') as temporary:
        root = Path(temporary)
        source = root / 'source'
        (source / 'src').mkdir(parents=True)
        (source / 'Cargo.toml').write_text(
            '[package]\nname="pump-recovered"\nversion="0.1.0"\nedition="2021"\n'
            '[lib]\ncrate-type=["cdylib"]\n'
            '[profile.release]\npanic="abort"\n[workspace]\n', encoding='utf-8')
        (source / 'Cargo.lock').write_text(
            'version = 3\n\n[[package]]\nname = "pump-recovered"\nversion = "0.1.0"\n',
            encoding='utf-8')
        (source / 'src/lib.rs').write_text(
            '#[no_mangle]\npub extern "C" fn proof_value() -> u64 { 42 }\n',
            encoding='utf-8')
        sdk = root / 'host-tools'
        (sdk / 'rust/bin').mkdir(parents=True)
        (sdk / 'rust/bin/cargo').symlink_to(cargo)
        recipes = {'host-proof': {'triple': host, 'rustc': Path(rustc),
                                  'template': root / 'absent-template'}}
        real_compiler = fastbuild.run_compiler
        for label, extra in (('clean', {}), ('override', {variable: str(root / 'absent-linker')})):
            observed = {}

            def compiler(*args, **kwargs):
                process, timed_out = real_compiler(*args, **kwargs)
                observed.update(returncode=process.returncode, timed_out=timed_out,
                                log=process.stdout.replace(str(root), '<proof-root>'))
                raise CompilerObserved

            # The host compiler needs bootstrap for the production recipe's
            # existing -Zremap-cwd-prefix flag. No SBF compiler is substituted.
            environment = {name: value for name, value in os.environ.items()
                           if not (name.startswith('CARGO_TARGET_') and name.endswith('_LINKER'))}
            environment.update(RUSTC_BOOTSTRAP='1', **extra)
            work, out = root / label, root / label / 'out'
            with patch.dict(os.environ, environment, clear=True), \
                 patch.object(fastbuild, 'SDK', sdk), \
                 patch.object(fastbuild, 'RECIPES', recipes), \
                 patch.object(fastbuild, 'LOCKDIR', root / 'slots'), \
                 patch.object(fastbuild, 'run_compiler', side_effect=compiler):
                try:
                    fastbuild.build(source, work, out, quiet=True, recipe='host-proof', timeout=60)
                except CompilerObserved:
                    pass
                else:
                    raise AssertionError('actual compiler was not observed')
            observed['source_sha256'] = json.loads((out / 'source-inputs.json').read_text())['sha256']
            if observed['returncode'] == 0:
                library = work / 'target-host-proof' / host / 'release/libpump_recovered.so'
                observed['elf_sha256'] = hashlib.sha256(library.read_bytes()).hexdigest()
                function = ctypes.CDLL(str(library)).proof_value
                function.restype = ctypes.c_uint64
                observed['proof_value'] = function()
            results['cases'][label] = observed
    return results


class AmbientLinkerTests(unittest.TestCase):
    def test_exported_linker_does_not_change_actual_compilation(self):
        result = native_probe()
        clean, override = (result['cases'][name] for name in ('clean', 'override'))
        self.assertEqual(clean['returncode'], 0, clean['log'])
        self.assertEqual(override['returncode'], 0, override['log'])
        self.assertFalse(clean['timed_out'] or override['timed_out'])
        self.assertEqual(clean['source_sha256'], override['source_sha256'])
        self.assertEqual(clean['proof_value'], 42)
        self.assertEqual(override['proof_value'], 42)
        self.assertEqual(clean['elf_sha256'], override['elf_sha256'])


if __name__ == '__main__':
    if sys.argv[1:] == ['--probe']:
        print(json.dumps(native_probe(), indent=2))
    else:
        unittest.main()
