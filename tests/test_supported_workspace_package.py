"""The selected manifest, rather than workspace defaults, chooses the package."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import test_supported_sbpf_entry_paths as fixtures


class SupportedPackageSelection(unittest.TestCase):
    def setUp(self):
        # Existing synthetic policy fixtures test planning only. Real compiler
        # behavior is established separately by the optional SDK probe below.
        self.fixture = fixtures.EntryPathTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        sibling = self.fixture.crate/'sibling'
        (sibling/'src').mkdir(parents=True)
        (sibling/'Cargo.toml').write_text('[package]\nname="sibling-package"\nversion="0.1.0"\n'
            '[lib]\nname="other_library"\ncrate-type=["cdylib"]\n', encoding='utf-8')
        (sibling/'src/lib.rs').write_text('// planning-only source\n', encoding='utf-8')

    def test_root_package_is_selected_independently_of_workspace_defaults(self):
        for defaults in ('', 'default-members=["."]\n', 'default-members=["sibling"]\n',
                         'default-members=[".","sibling"]\n'):
            with self.subTest(defaults=defaults):
                text = fixtures.TOML.replace('name="fixture"', 'name="selected-root-package"').replace(
                    '[workspace]', '[workspace]\nmembers=["sibling"]\n'+defaults)
                planned = self.fixture.plan(text)
                command = planned['command']
                self.assertEqual(command.count('--package'), 1)
                self.assertEqual(command[command.index('--package')+1], 'selected-root-package')
                self.assertTrue(planned['compiled_binary'].endswith('/fixture_lib.so'))
                self.assertFalse(self.fixture.output.exists())

    def test_member_manifest_selects_its_own_package(self):
        (self.fixture.crate/'Cargo.toml').write_text(fixtures.TOML.replace(
            '[workspace]', '[workspace]\nmembers=["sibling"]\ndefault-members=["."]\n'), encoding='utf-8')
        module = fixtures.adapter()
        args = module.parser().parse_args(['--manifest', str(self.fixture.crate/'sibling/Cargo.toml'),
            '--program', 'pump', '--artifact-name', 'candidate.so', '--tools-version', 'v1.53',
            '--output', str(self.fixture.output), '--extra-input', str(self.fixture.crate), '--dry-run'])
        planned = module.plan(args, self.fixture.repo, self.fixture.env,
                              cache_root=self.fixture.tools, policy_directory=self.fixture.policies)
        command = planned['command']
        self.assertEqual(command[command.index('--package')+1], 'sibling-package')
        self.assertTrue(planned['compiled_binary'].endswith('/other_library.so'))
        self.assertFalse(self.fixture.output.exists())

    @unittest.skipUnless(sys.platform == 'darwin' and os.environ.get('PUMP_SUPPORTED_TEST_TOOLS'),
                         'requires official v1.53 SDK and pinned v1.52 objcopy')
    def test_actual_offline_compiler_package_selection(self):
        path = ROOT/'research/supported-workspace-package-20261101/probe.py'
        spec = importlib.util.spec_from_file_location('supported_package_sdk_probe', path)
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)
        with tempfile.TemporaryDirectory() as temporary:
            record = probe.run(ROOT, Path(os.environ['PUMP_SUPPORTED_TEST_TOOLS']), Path(temporary)/'proof')
        probe.validate(record, 'fixed')
        self.assertEqual(len(record['cases']), 7)


if __name__ == '__main__':
    unittest.main()
