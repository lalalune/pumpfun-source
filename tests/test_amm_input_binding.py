"""AMM attempt keys and the actual staged/linker bytes must describe one input."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/amm_sell'))
import try_sell as runner
import native_build

LLD = os.environ.get('PUMP_TEST_LLD') or shutil.which('ld.lld')
CLANG = os.environ.get('PUMP_TEST_CLANG') or shutil.which('clang')


class InputBindingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='amm-input-binding-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.baseline = self.root / 'baselines/pristine-ws'
        sell = self.baseline / native_build.SELL_REL
        sell.parent.mkdir(parents=True); sell.write_bytes(b'// value 7\n')
        original = self.root / 'infra/original/deployed.so'
        original.parent.mkdir(parents=True); original.write_bytes(b'context input')
        context = patch.multiple(runner, SWARM=self.root, SOURCES=self.root / 'sources', CACHE=self.root / 'cache')
        context.start(); self.addCleanup(context.stop)

    def admit(self, **kwargs):
        return runner.input_snapshot(self.baseline, sell=None, patch=None, flags='',
                                     link_script=kwargs.get('link_script'), want_disasm=False)

    def test_empty_override_is_distinct_from_default_linker_script(self):
        empty = self.root / 'empty.ld'; empty.write_bytes(b'')
        default, _ = self.admit()
        override, _ = self.admit(link_script=empty)
        self.assertIsNone(default['link'])
        self.assertEqual(override['link'], runner.sha(b''))
        self.assertNotEqual(default, override)

    @unittest.skipUnless(shutil.which('rsync') and shutil.which('patch'), 'requires actual POSIX staging tools')
    def test_real_attempt_staging_uses_admitted_sell_patch_and_link_bytes(self):
        for mode in ('sell', 'patch'):
            with self.subTest(mode=mode):
                selected = self.root / (mode + '.input')
                admitted = (b'// value 8\n' if mode == 'sell' else
                            ('--- a/' + native_build.SELL_REL + '\n+++ b/' + native_build.SELL_REL +
                             '\n@@ -1 +1 @@\n-// value 7\n+// value 8\n').encode())
                selected.write_bytes(admitted)
                script = self.root / 'override.ld'; script.write_bytes(b'admitted linker script\n')
                original_snapshot = runner.input_snapshot
                original_run = subprocess.run
                compiler_environments = []

                def mutate_after_admission(*args, **kwargs):
                    result = original_snapshot(*args, **kwargs)
                    selected.write_bytes(admitted.replace(b'value 8', b'value 9'))
                    script.write_bytes(b'later linker script\n')
                    return result

                def observe_actual_process(command, **kwargs):
                    if Path(command[0]).name == 'cargo':
                        compiler_environments.append(kwargs['env'])
                    return original_run(command, **kwargs)

                arguments = ['try_sell.py', '--lane', mode, '--approach', 'binding', '--hypothesis', 'probe',
                             '--' + mode, str(selected), '--link-script', str(script)]
                with patch.object(runner, 'input_snapshot', side_effect=mutate_after_admission), \
                        patch.object(native_build, 'PRISTINE', self.baseline), \
                        patch.object(native_build, 'SEED_TARGET', self.root / 'absent-seed'), \
                        patch.object(native_build, 'SDK', self.root / 'absent-sdk'), \
                        patch.object(subprocess, 'run', side_effect=observe_actual_process), \
                        patch.object(sys, 'argv', arguments), self.assertRaises(FileNotFoundError):
                    # The real recipe, rsync and patch run; only an absent SDK
                    # stops execution at the compiler boundary. No fake success.
                    runner.main()
                self.assertEqual((self.root / 'lanes' / mode / 'build0/ws' / native_build.SELL_REL).read_bytes(),
                                 b'// value 8\n')
                self.assertEqual(len(compiler_environments), 1)
                retained_script = Path(compiler_environments[0]['AMM_LINK_SCRIPT'])
                self.assertNotEqual(retained_script, script)
                self.assertEqual(retained_script.read_bytes(), b'admitted linker script\n')

    @unittest.skipUnless(LLD and CLANG, 'requires real LLVM linker and Clang')
    def test_real_linker_output_follows_admitted_script(self):
        script = ROOT / 'research/amm-input-binding-20261031/probe.py'
        result = subprocess.run([sys.executable, str(script), str(ROOT), LLD, CLANG],
                                capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stderr)
        default, empty, changed = json.loads(result.stdout)['rows']
        self.assertNotEqual(default['key'], empty['key'])
        self.assertNotEqual(default['candidate_sha256'], empty['candidate_sha256'])
        self.assertEqual(changed['admitted_link_sha256'], changed['used_link_sha256'])
        self.assertEqual(changed['candidate_sha256'], default['candidate_sha256'])


if __name__ == '__main__':
    unittest.main()
