"""Exercise installed policy source pins through the real, filesystem-only planner.

Host facts are modeled as Darwin/arm64 and SDK files are inert, hash-pinned
fixtures. No native compiler qualification or compiler execution is claimed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

import build_supported_sbpf_candidate as builder

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SupportedPolicySourceBinding(unittest.TestCase):
    def fixture(self, version):
        temporary = tempfile.TemporaryDirectory(prefix='installed-policy-source-')
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        repo, native, cache, policies = (base / name for name in ('repo', 'native', 'cache', 'policies'))
        (repo / 'crate/src').mkdir(parents=True)
        (repo / 'scripts').mkdir()
        (cache / 'registry').mkdir(parents=True)
        policies.mkdir()
        shutil.copyfile(HERE / 'build_source_manifest.py', repo / 'scripts/build_source_manifest.py')
        (repo / 'Cargo.toml').write_text('[workspace]\nmembers=["crate"]\n[profile.release]\npanic="abort"\noverflow-checks=true\nlto=false\ncodegen-units=1\n')
        (repo / 'Cargo.lock').write_text('version=3\n')
        (repo / 'crate/Cargo.toml').write_text('[package]\nname="fixture"\nversion="0.1.0"\n[lib]\nname="fixture_lib"\ncrate-type=["cdylib"]\n')
        (repo / 'crate/src/lib.rs').write_text('pub fn fixture() {}\n')
        policy = json.loads((HERE / 'supported_sbpf_policies' / (version + '.json')).read_bytes())
        # Preserve the actual installed source-inventory pin. Only SDK/strip
        # digests are adapted to owned inert files so planning needs no SDK.
        tools = native / version / 'platform-tools'
        for relative in policy['selected_files']:
            path = tools / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('inert fixture: ' + relative)
        for relative, record in policy['extra_environment_tools'].items():
            path, target = tools / relative, tools / record['resolved_relative_path']
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_text('inert fixture: ' + record['resolved_relative_path'])
            path.parent.mkdir(parents=True, exist_ok=True)
            if path != target:
                path.unlink(missing_ok=True)
                path.symlink_to(target)
        for relative, record in policy['selected_files'].items():
            record['sha256'] = sha(tools / relative)
        for relative, record in policy['extra_environment_tools'].items():
            record['sha256'] = sha(tools / relative)
        strip = native / policy['strip_tools_version'] / 'platform-tools/llvm/bin/llvm-objcopy'
        strip.parent.mkdir(parents=True, exist_ok=True)
        strip.write_text('inert strip fixture')
        policy['strip_sha256'] = sha(strip)
        (policies / (version + '.json')).write_text(json.dumps(policy))
        args = argparse.Namespace(manifest=repo / 'crate/Cargo.toml', output=base / 'output',
                                  artifact_name='fixture.so', tools_version=version,
                                  program='pump', extra_input=[], dry_run=True)
        return args, repo, native, cache, policies

    def plan(self, fixture):
        args, repo, native, cache, policies = fixture
        with mock.patch.object(builder.platform, 'system', return_value='Darwin'), \
                mock.patch.object(builder.platform, 'machine', return_value='arm64'):
            result = builder.plan(args, repo, {'CARGO_HOME': str(cache)},
                                  cache_root=native, policy_directory=policies)
        self.assertFalse(args.output.exists(), 'planning wrote build output')
        return result

    def test_installed_v153_policy_can_plan_the_current_source_contract(self):
        result = self.plan(self.fixture('v1.53'))
        self.assertTrue(result['dry_run'])
        self.assertIn('--offline', result['command'])
        self.assertEqual(set(result['source_sha256']),
                         {'Cargo.toml', 'Cargo.lock', 'crate/Cargo.toml', 'crate/src/lib.rs'})

    def test_installed_v154_policy_can_plan_the_current_source_contract(self):
        result = self.plan(self.fixture('v1.54'))
        self.assertEqual(result['program'], 'pump')
        self.assertEqual(set(result['source_sha256']),
                         {'Cargo.toml', 'Cargo.lock', 'crate/Cargo.toml', 'crate/src/lib.rs'})

    def test_changed_source_utility_is_still_refused(self):
        fixture = self.fixture('v1.53')
        utility = fixture[1] / 'scripts/build_source_manifest.py'
        utility.write_bytes(utility.read_bytes() + b'\n# unreviewed change\n')
        with self.assertRaisesRegex(ValueError, 'source manifest utility changed'):
            self.plan(fixture)

    def test_current_nested_target_module_is_bound_in_the_plan(self):
        fixture = self.fixture('v1.53')
        module = fixture[1] / 'crate/src/target/helper.rs'
        module.parent.mkdir()
        module.write_text('pub fn helper() {}\n')
        (fixture[1] / 'crate/src/lib.rs').write_text('mod target { pub mod helper; }\n')
        result = self.plan(fixture)
        self.assertEqual(result['source_sha256']['crate/src/target/helper.rs'], sha(module))

    def test_changed_sdk_input_is_still_refused(self):
        fixture = self.fixture('v1.54')
        tools = fixture[2] / 'v1.54/platform-tools'
        (tools / 'version.md').write_text('changed SDK fixture')
        with self.assertRaisesRegex(ValueError, 'measured tool/sysroot bytes differ'):
            self.plan(fixture)


if __name__ == '__main__':
    unittest.main()
