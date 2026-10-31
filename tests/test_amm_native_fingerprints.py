"""Real Cargo rebuilds local source despite future-dated retained fingerprints."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('amm_native_fingerprints', ROOT / 'scripts/amm_sell/native_build.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)
RUST_BIN = Path(os.environ['PUMP_TEST_RUST_BIN']) if os.environ.get('PUMP_TEST_RUST_BIN') else (
    Path(shutil.which('rustc')).parent if shutil.which('rustc') else None)


class LocalFingerprintTests(unittest.TestCase):
    def test_external_fingerprints_and_artifacts_are_retained(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            retained = []
            for release in ('release', 'sbpf-solana-solana/release'):
                for name in ('pump-amm-recovered-1234', 'native-transfer-fee-abcd', 'external-package-5678'):
                    directory = target / release / '.fingerprint' / name
                    directory.mkdir(parents=True)
                    (directory / 'fingerprint').write_bytes(b'retained cache metadata')
                    if name.startswith('external'):
                        retained.append(directory / 'fingerprint')
                artifact = target / release / 'deps/libexternal.rlib'
                artifact.parent.mkdir()
                artifact.write_bytes(b'retained dependency artifact')
                retained.append(artifact)
            native.invalidate_local_crates(target)
            self.assertTrue(all(path.is_file() for path in retained))
            self.assertEqual(len(list(target.glob('**/.fingerprint/*'))), 2)

    @unittest.skipUnless(RUST_BIN and (RUST_BIN / 'cargo').is_file(), 'requires Cargo/rustc or PUMP_TEST_RUST_BIN')
    def test_real_cargo_rebuilds_both_local_packages_after_clock_skew(self):
        rustc, cargo = RUST_BIN / 'rustc', RUST_BIN / 'cargo'
        host = next(line.split(': ', 1)[1] for line in subprocess.check_output(
            [str(rustc), '-vV'], text=True).splitlines() if line.startswith('host: '))
        for explicit_target in (False, True):
            with self.subTest(explicit_target=explicit_target), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                workspace, target = root / 'workspace', root / 'target'
                main, local = workspace / 'programs/pump-amm', workspace / 'crates/native-transfer-fee'
                for crate in (main, local):
                    (crate / 'src').mkdir(parents=True)
                (workspace / 'Cargo.toml').write_text('[workspace]\nmembers=["programs/pump-amm","crates/native-transfer-fee"]\nresolver="2"\n')
                (main / 'Cargo.toml').write_text('[package]\nname="pump-amm-recovered"\nversion="0.1.0"\nedition="2021"\n[dependencies]\nnative-transfer-fee={path="../../crates/native-transfer-fee"}\n')
                (local / 'Cargo.toml').write_text('[package]\nname="native-transfer-fee"\nversion="0.1.0"\nedition="2021"\n')
                (main / 'src/main.rs').write_text('fn main(){println!("{}",native_transfer_fee::value());}\n')
                leaf = local / 'src/lib.rs'
                leaf.write_text('pub fn value()->u64{1}\n')
                env = dict(os.environ, CARGO_HOME=str(root / 'cargo-home'), CARGO_TARGET_DIR=str(target), RUSTC=str(rustc))
                for key in ('RUSTC_WRAPPER', 'RUSTC_WORKSPACE_WRAPPER', 'CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER'):
                    env.pop(key, None)
                command = [str(cargo), 'build', '--release', '--offline']
                if explicit_target:
                    command += ['--target', host]
                first = subprocess.run(command, cwd=workspace, env=env, capture_output=True, text=True, timeout=60)
                self.assertEqual(first.returncode, 0, first.stderr)
                release = target / host / 'release' if explicit_target else target / 'release'
                binary = release / ('pump-amm-recovered.exe' if os.name == 'nt' else 'pump-amm-recovered')
                self.assertEqual(subprocess.check_output([str(binary)], text=True).strip(), '1')
                future = time.time() + 3600
                for path in (release / '.fingerprint').rglob('*'):
                    if path.is_file():
                        os.utime(path, (future, future))
                leaf.write_text('pub fn value()->u64{2}\n')
                (main / 'src/main.rs').write_text('fn main(){println!("{}",native_transfer_fee::value()+10);}\n')
                native.invalidate_local_crates(target)
                second = subprocess.run(command + ['--locked'], cwd=workspace, env=env, capture_output=True, text=True, timeout=60)
                self.assertEqual(second.returncode, 0, second.stderr)
                self.assertEqual(subprocess.check_output([str(binary)], text=True).strip(), '12')


if __name__ == '__main__':
    unittest.main()
