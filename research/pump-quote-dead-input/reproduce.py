"""Build actual Pump and replay the unchanged 130-case quote CLI without repro/."""
import ast
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

if not __debug__:
    raise SystemExit("quote reproduction requires Python assertions; omit -O/-OO")

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT / 'work/scoped-proof'
PROOF.mkdir(parents=True, exist_ok=True)
SDK = Path.home() / '.cache/solana/v1.44/platform-tools'
env = dict(os.environ, CARGO_REGISTRIES_CRATES_IO_PROTOCOL='sparse',
           CARGO_BUILD_JOBS='2', RUSTC=str(SDK / 'rust/bin/rustc'))


def run(name, command):
    with (PROOF / (name + '.log')).open('w') as log:
        return subprocess.run(command, cwd=ROOT, env=env, stdout=log,
                              stderr=subprocess.STDOUT, timeout=1000).returncode


assert not (ROOT / 'repro/pump/constant-product-differential.json').exists()
script = ROOT / 'scripts/pump_validate_quote.py'
tree = ast.parse(script.read_text())
reset = max(i for i, node in enumerate(tree.body) if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == 'cases' for t in node.targets)
            and isinstance(node.value, ast.List) and not node.value.elts)
stop = next(i for i in range(reset + 1, len(tree.body)) if isinstance(tree.body[i], ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == 'rows' for t in tree.body[i].targets))
pieces = {'actual_case_generator': ast.Module(body=tree.body[reset:stop], type_ignores=[]),
          'actual_vm_run_function': next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'run')}
shape = {name: hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
         for name, node in pieces.items()}
(PROOF / 'unchanged-logic.json').write_text(json.dumps(shape, indent=2) + '\n')

if sys.platform == 'linux':
    # Keep the proof extraction separate from the user's installed SDK.
    SDK = ROOT / 'work/quote-native-sdk'
    env['RUSTC'] = str(SDK / 'rust/bin/rustc')
    from native_sdk import prepare
    target_arguments = prepare(ROOT, SDK, PROOF)
else:
    libraries = ROOT / 'work/quote-target-libraries'
    shutil.copytree(ROOT / 'reconstruction/toolchain/linux-v1.44-x86_64/rust/lib/rustlib/sbpf-solana-solana/lib', libraries)
    (libraries / 'self-contained').mkdir(exist_ok=True)
    target_arguments = ['--target', 'sbpf-solana-solana', '--target-library-profile', 'linux-v1.44-sbpf',
                        '--target-library-directory', str(libraries)]

assert run('fetch', [str(SDK / 'rust/bin/cargo'), 'fetch', '--locked',
                    '--manifest-path', str(ROOT / 'programs/pump/Cargo.toml')]) == 0
build = ROOT / 'work/quote-build'
assert run('build', [sys.executable, '-B', 'scripts/pump_build_verified.py',
            '--sdk', str(SDK), '--source-directory', str(ROOT / 'programs/pump'),
            *target_arguments, '--workspace-layout',
            '--output', str(build)]) == 0
for filename in ('build-attempt.json', 'build-comparison.json', 'build.log'):
    shutil.copyfile(build / filename, PROOF / filename)
for filename in ('candidate.so', 'unstripped.so'):
    (PROOF / (filename + '.gz')).write_bytes(gzip.compress((build / filename).read_bytes(), mtime=0))

command = [sys.executable, '-B', str(script), '--source-directory', str(build / 'source/programs/pump')]
positive = PROOF / 'positive.json.gz'
code = run('positive', command + ['--candidate', str(build / 'candidate.so'), '--output', str(positive)])
(PROOF / 'entry.json').write_text(json.dumps({'actual_cli_returncode': code,
                                             'output_exists': positive.is_file()}, indent=2) + '\n')
assert code == 0 and positive.is_file(), 'quote CLI is blocked by a discarded predecessor input'
result = json.loads(gzip.decompress(positive.read_bytes()))
assert result['case_count'] == len(result['cases']) == 130 and not result['mismatches']
assert all(not row['different_fields'] for row in result['cases'])
assert not (ROOT / 'repro/pump/constant-product-differential.json').exists()
negative = PROOF / 'negative.json.gz'
negative_code = run('negative', command + ['--candidate', str(ROOT / 'evidence/original/mayhem/deployed.so'),
                                          '--output', str(negative)])
rejected = json.loads(gzip.decompress(negative.read_bytes()))
assert negative_code != 0 and len(rejected['cases']) == 130 and rejected['mismatches']
summary = {'actual_candidate_sha256': result['candidate_sha256'], 'cases': 130,
           'matching_cases': 130, 'legacy_input_absent': True, 'logic_sha256': shape,
           'wrong_program_returncode': negative_code, 'wrong_program_mismatches': len(rejected['mismatches'])}
(PROOF / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
