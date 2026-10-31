"""A source helper's owner execute bit changes real Cargo build behavior."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from source_inputs import snapshot, assert_unchanged


@unittest.skipUnless(os.name == 'posix' and os.geteuid() != 0 and shutil.which('cargo') and shutil.which('rustc'),
                     'requires non-root POSIX host Cargo and rustc')
class SourceExecuteBitsTests(unittest.TestCase):
    def test_real_cargo_distinguishes_execute_permission_classes(self):
        with tempfile.TemporaryDirectory(prefix='source-execute-bits-') as temporary:
            root = Path(temporary)
            source = root / 'source'
            (source / 'src').mkdir(parents=True)
            (source / 'Cargo.toml').write_text('[package]\nname="execute_bits_probe"\nversion="0.1.0"\nedition="2021"\n[workspace]\n')
            (source / 'src/main.rs').write_text('fn main() {}\n')
            (source / 'build.rs').write_text(
                'fn main(){let result=std::process::Command::new("./helper.sh").status()'
                '.expect("execute helper");assert!(result.success());}\n')
            helper = source / 'helper.sh'
            helper.write_text('#!/bin/sh\nexit 0\n')
            environment = dict(os.environ, CARGO_HOME=str(root / 'cargo-home'))
            for key in ('RUSTC_WRAPPER', 'RUSTC_WORKSPACE_WRAPPER', 'CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER'):
                environment.pop(key, None)
            subprocess.run(['cargo', 'generate-lockfile', '--offline'], cwd=source,
                           env=environment, capture_output=True, check=True)
            receipts, results = [], []
            for mode in (0o755, 0o645, 0o644):
                helper.chmod(mode)
                receipts.append(snapshot(source))
                results.append(subprocess.run(
                    ['cargo', 'build', '--offline', '--locked', '--target-dir', str(root / str(mode))],
                    cwd=source, env=environment, capture_output=True, text=True))
            self.assertEqual(results[0].returncode, 0, results[0].stderr)
            for result in results[1:]:
                self.assertEqual(result.returncode, 101, result.stderr)
                self.assertIn('PermissionDenied', result.stderr)
            self.assertEqual(len({receipt['sha256'] for receipt in receipts}), 3)
            with self.assertRaisesRegex(ValueError, 'helper.sh'):
                # Current source differs from both executable variants.
                assert_unchanged(source, receipts[1])
            helper.chmod(0o645)
            with self.assertRaisesRegex(ValueError, 'helper.sh'):
                assert_unchanged(source, receipts[0])
            helper.chmod(0o755)
            os.utime(helper, (1, 1))
            self.assertEqual(snapshot(source), receipts[0])


if __name__ == '__main__':
    unittest.main()
