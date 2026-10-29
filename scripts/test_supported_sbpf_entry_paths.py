"""Cross-host Cargo entry-path escape regressions for the installed supported-SBPF adapter.

Cargo manifests are copied with their literal spelling, so an explicit target/build
reference can be POSIX-absolute while the planner runs on Windows, or Windows-absolute
while it runs on POSIX. The planner must reject the reference as written on either host.

Synthetic manifests here use repository-free absolute paths and the pinned source-inventory
utility, so the cases do not depend on the sealed proposal packet or on a sparse checkout.
The shared policy test file is unchanged and keeps its own inherited cases.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import platform
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOML = ('[package]\nname="fixture"\nversion="0.1.0"\n[lib]\nname="fixture_lib"\n'
        'crate-type=["cdylib"]\n[workspace]\n[profile.release]\npanic="abort"\n'
        'overflow-checks=true\nlto=false\ncodegen-units=1\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def adapter():
    spec = importlib.util.spec_from_file_location('installed_supported_adapter_entry_paths',
                                                  ROOT / 'scripts/build_supported_sbpf_candidate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EntryPathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.repo = base / 'repo'
        self.crate = self.repo / 'programs/mayhem'
        (self.crate / 'src').mkdir(parents=True)
        (self.repo / 'scripts').mkdir()
        shutil.copyfile(ROOT / 'scripts/build_source_manifest.py', self.repo / 'scripts/build_source_manifest.py')
        (self.crate / 'Cargo.toml').write_text(TOML)
        (self.crate / 'Cargo.lock').write_text('version = 3\n')
        (self.crate / 'src/lib.rs').write_text('// synthetic source fixture\n')
        cache = base / 'cache'
        (cache / 'registry').mkdir(parents=True)
        self.tools = base / 'tools'
        self.policies = base / 'policies'
        self.policies.mkdir()
        selected = {}
        for name in ('rust/bin/rustc', 'rust/bin/cargo'):
            tool = self.tools / 'v1.53/platform-tools' / name
            tool.parent.mkdir(parents=True, exist_ok=True)
            tool.write_text(name + ' synthetic, not executable')
            selected[name] = {'sha256': sha(tool)}
        strip = self.tools / 'v1.52/platform-tools/llvm/bin/llvm-objcopy'
        strip.parent.mkdir(parents=True)
        strip.write_text('synthetic strip fixture')
        policy = {'selected_files': selected, 'extra_environment_tools': {}, 'strip_tools_version': 'v1.52',
                  'strip_sha256': sha(strip), 'target': 'sbpf-solana-solana',
                  'target_rustflags': '-Zremap-cwd-prefix=',
                  'source_inventory_utility_sha256': sha(self.repo / 'scripts/build_source_manifest.py'),
                  'measured_host': {'system': platform.system(), 'machine': platform.machine()}}
        (self.policies / 'v1.53.json').write_text(json.dumps(policy))
        self.env = {'CARGO_HOME': str(cache)}
        self.output = base / 'out'

    def plan(self, manifest, extra_inputs=()):
        (self.crate / 'Cargo.toml').write_text(manifest)
        module = adapter()
        arguments = ['--manifest', str(self.crate / 'Cargo.toml'), '--program', 'mayhem',
                     '--artifact-name', 'result.so', '--tools-version', 'v1.53',
                     '--output', str(self.output), '--dry-run']
        for extra in extra_inputs:
            arguments += ['--extra-input', str(extra)]
        return module.plan(module.parser().parse_args(arguments), self.repo, self.env,
                           cache_root=self.tools, policy_directory=self.policies)

    def rejected(self, manifest):
        with self.assertRaisesRegex(ValueError, 'absolute Cargo target/build'):
            self.plan(manifest)
        self.assertFalse(self.output.exists())

    def with_build(self, reference):
        return TOML.replace('version="0.1.0"', 'version="0.1.0"\nbuild = "' + reference + '"')

    def test_posix_absolute_build_script_rejected_on_every_host(self):
        for reference in ('/tmp/unrecorded.rs', '/unrecorded.rs', '//unrecorded.rs'):
            with self.subTest(reference=reference):
                self.rejected(self.with_build(reference))

    def test_posix_absolute_lib_and_bin_paths_rejected_on_every_host(self):
        self.rejected(TOML.replace('name="fixture_lib"', 'name="fixture_lib"\npath="/tmp/unrecorded.rs"'))
        self.rejected(TOML + '\n[[bin]]\nname="unrecorded"\npath="/unrecorded.rs"\n')

    def test_windows_drive_paths_rejected_on_every_host(self):
        manifest = TOML.replace('name="fixture_lib"', 'name="fixture_lib"\npath="C:/unrecorded.rs"')
        manifest += '\n[[bin]]\nname="unrecorded"\npath="D:\\\\unrecorded.rs"\n'
        self.rejected(manifest)

    def test_windows_drive_relative_build_script_rejected_on_every_host(self):
        # A POSIX filename with a Windows drive prefix is a relative filename
        # here, but Windows Cargo resolves it through that drive's current
        # directory rather than the copied crate.
        reference = 'C:recorded-drive-relative.rs'
        (self.crate / reference).write_text('// recorded POSIX-only filename\n')
        self.rejected(self.with_build(reference))

    def test_windows_unc_build_script_rejected_on_every_host(self):
        self.rejected(self.with_build('\\\\\\\\server\\\\share\\\\unrecorded.rs'))

    def test_windows_root_relative_recorded_entry_rejected(self):
        # Modern ntpath.isabs rejects only fully absolute Windows paths, so
        # recording this literal filename on POSIX used to bypass the check.
        reference = "\\recorded-root-relative.rs"
        if not Path(reference).anchor:
            (self.crate / reference).write_text('// recorded synthetic entry\n')
        self.rejected(self.with_build(reference.replace("\\", "\\\\")))

    def test_relative_parent_escape_uses_snapshot_check(self):
        with self.assertRaisesRegex(ValueError, 'outside the recorded snapshot'):
            self.plan(TOML.replace('name="fixture_lib"', 'name="fixture_lib"\npath="../unrecorded.rs"'))
        self.assertFalse(self.output.exists())

    def test_recorded_relative_entry_still_plans(self):
        planned = self.plan(TOML.replace('name="fixture_lib"', 'name="fixture_lib"\npath="src/lib.rs"'))
        self.assertIn('programs/mayhem/src/lib.rs', planned['source_sha256'])
        self.assertFalse(self.output.exists())

    def helper(self):
        helper = self.repo / 'crates/helper'
        (helper / 'src').mkdir(parents=True)
        (helper / 'Cargo.toml').write_text('[package]\nname="helper"\nversion="0.1.0"\n')
        (helper / 'src/lib.rs').write_text('// synthetic dependency fixture\n')
        return helper

    def test_absolute_path_dependency_rejected_on_every_host(self):
        # The copied manifest keeps the literal path, so even a recorded in-repo
        # dependency would be compiled from the live tree, not the snapshot.
        helper = self.helper()
        for reference in (helper.as_posix(), '/tmp/elsewhere', 'C:/elsewhere', 'C:elsewhere', '\\\\server\\share\\dep'):
            with self.subTest(reference=reference):
                with self.assertRaisesRegex(ValueError, 'absolute Cargo path dependencies'):
                    self.plan(TOML + '[dependencies]\nhelper={path=\'' + reference + '\'}\n', [helper])
                self.assertFalse(self.output.exists())

    def test_relative_path_dependency_escape_rejected(self):
        with self.assertRaisesRegex(ValueError, 'path dependency is outside the recorded snapshot'):
            self.plan(TOML + '[dependencies]\nhelper={path="../../../elsewhere"}\n')
        self.assertFalse(self.output.exists())

    def test_package_metadata_path_is_not_a_dependency(self):
        planned = self.plan(TOML + '[package.metadata.tool]\npath="/usr/share/tool"\n')
        self.assertIn('programs/mayhem/Cargo.toml', planned['source_sha256'])

    def test_recorded_relative_path_dependency_still_plans(self):
        helper = self.helper()
        planned = self.plan(TOML + '[dependencies]\nhelper={path="../../crates/helper"}\n', [helper])
        self.assertIn('crates/helper/Cargo.toml', planned['source_sha256'])
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
