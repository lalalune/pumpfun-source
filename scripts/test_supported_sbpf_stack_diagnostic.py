"""The SBF backend can report a frame overflow and still return zero."""
from pathlib import Path
import hashlib
import importlib.util
import json
import platform
import shutil
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOML = ('[package]\nname="fixture"\nversion="0.1.0"\n[lib]\nname="fixture_lib"\n'
        'crate-type=["cdylib"]\n[workspace]\n[profile.release]\npanic="abort"\n'
        'overflow-checks=true\nlto=false\ncodegen-units=1\n')
DIAGNOSTIC = ('Error: Function probe Stack offset of -8192 exceeded max offset of -4096 by 4096 bytes, '
              'please minimize large stack variables. Estimated function frame size: 8192 bytes.\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def adapter():
    spec = importlib.util.spec_from_file_location('supported_adapter_stack_diagnostic',
                                                  ROOT / 'scripts/build_supported_sbpf_candidate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StackDiagnostic(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'repo'
        crate = self.repo / 'programs/mayhem'
        (crate / 'src').mkdir(parents=True)
        (self.repo / 'scripts').mkdir()
        (self.repo / 'evidence/original/mayhem').mkdir(parents=True)
        (self.repo / 'evidence/original/mayhem/deployed.so').write_bytes(b'original')
        shutil.copyfile(ROOT / 'scripts/build_source_manifest.py', self.repo / 'scripts/build_source_manifest.py')
        (crate / 'Cargo.toml').write_text(TOML)
        (crate / 'Cargo.lock').write_text('version = 3\n')
        (crate / 'src/lib.rs').write_text('// synthetic source fixture\n')
        (self.base / 'cache/registry').mkdir(parents=True)
        tools, policies = self.base / 'tools', self.base / 'policies'
        policies.mkdir()
        selected = {}
        for name in ('rust/bin/rustc', 'rust/bin/cargo'):
            tool = tools / 'v1.53/platform-tools' / name
            tool.parent.mkdir(parents=True, exist_ok=True)
            tool.write_text(name)
            selected[name] = {'sha256': sha(tool)}
        strip = tools / 'v1.52/platform-tools/llvm/bin/llvm-objcopy'
        strip.parent.mkdir(parents=True)
        strip.write_text('strip')
        (policies / 'v1.53.json').write_text(json.dumps({
            'selected_files': selected, 'extra_environment_tools': {}, 'strip_tools_version': 'v1.52',
            'strip_sha256': sha(strip), 'target': 'sbpf-solana-solana', 'target_rustflags': '-Zremap-cwd-prefix=',
            'source_inventory_utility_sha256': sha(self.repo / 'scripts/build_source_manifest.py'),
            'measured_host': {'system': platform.system(), 'machine': platform.machine()}}))
        self.module = adapter()
        self.env = {'CARGO_HOME': str(self.base / 'cache')}
        arguments = ['--manifest', str(crate / 'Cargo.toml'), '--program', 'mayhem', '--artifact-name', 'result.so',
                     '--tools-version', 'v1.53', '--output', str(self.base / 'out')]
        self.planned = self.module.plan(self.module.parser().parse_args(arguments), self.repo, self.env,
                                        cache_root=tools, policy_directory=policies)
        self.output = self.base / 'out'

    def execute(self, log_text):
        image = bytearray(b'\x7fELF\x02\x01'.ljust(64, b'\0'))
        struct.pack_into('<H', image, 18, 263)

        def runner(command, **options):
            if '--strip-all' in command:
                Path(self.planned['artifact']).write_bytes(image)
            else:
                options['stdout'].write(log_text)
                compiled = Path(self.planned['compiled_binary'])
                compiled.parent.mkdir(parents=True, exist_ok=True)
                compiled.write_bytes(image)
            return type('Completed', (), {'returncode': 0})()

        return self.module.execute(self.planned, self.env, runner=runner)

    def test_reported_frame_overflow_is_not_published(self):
        code = self.execute('Compiling fixture\n' + DIAGNOSTIC)
        self.assertNotEqual(code, 0)
        self.assertFalse((self.output / 'build-comparison.json').exists())
        self.assertFalse((self.output / 'unstripped.so').exists())
        attempt = json.loads((self.output / 'build-attempt.json').read_text(encoding='utf-8'))
        self.assertEqual(attempt['stack_warnings'], [DIAGNOSTIC.strip()])
        self.assertFalse(attempt['stack_diagnostic_gate_passed'])

    def test_clean_log_still_publishes(self):
        self.assertEqual(self.execute('warning: overwrites values in the frame\n'), 0)
        report = json.loads((self.output / 'build-comparison.json').read_text(encoding='utf-8'))
        self.assertIs(report.get('stack_diagnostic_gate_passed'), True)


if __name__ == '__main__':
    unittest.main()
