"""Exercise the serial driver's actual two-curve dispatch with a fresh build.

The primary bounded proof runs the unchanged 20-case real-LiteSVM child. It
does not claim a complete 44-suite run. Set SERIAL_FULL_CORPUS=1 to additionally
run the complete serial CLI. No child outputs or producer receipts are mocked.
"""
if not __debug__:
    raise SystemExit('Use normal Python for this reproduction')

import argparse
import ast
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT / 'work/scoped-proof'
PROOF.mkdir(parents=True, exist_ok=True)
SDK = ROOT / 'work/serial-native-sdk'
env = dict(os.environ, CARGO_REGISTRIES_CRATES_IO_PROTOCOL='sparse',
           CARGO_BUILD_JOBS='2', RUSTC=str(SDK / 'rust/bin/rustc'))


def run(name, command, timeout=1500):
    with (PROOF / (name + '.log')).open('w', encoding='utf-8') as stream:
        return subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                              stderr=subprocess.STDOUT, timeout=timeout).returncode


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


sdk_helper = ROOT / 'research/pump-quote-dead-input/native_sdk.py'
spec = importlib.util.spec_from_file_location('native_sdk', sdk_helper)
native_sdk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native_sdk)
target = native_sdk.prepare(ROOT, SDK, PROOF)
assert run('fetch', [str(SDK / 'rust/bin/cargo'), 'fetch', '--locked',
                    '--manifest-path', str(ROOT / 'programs/pump/Cargo.toml')]) == 0
build = ROOT / 'work/serial-current-build'
assert run('build', [sys.executable, '-B', 'scripts/pump_build_verified.py',
                    '--sdk', str(SDK), '--source-directory', str(ROOT / 'programs/pump'),
                    *target, '--workspace-layout', '--output', str(build)]) == 0
for name in ('build-attempt.json', 'build-comparison.json', 'build.log'):
    shutil.copyfile(build / name, PROOF / name)
for name in ('candidate.so', 'unstripped.so'):
    (PROOF / (name + '.gz')).write_bytes(gzip.compress((build / name).read_bytes(), mtime=0))

sys.path.insert(0, str(ROOT / 'scripts'))
import pump_validate_all as serial

candidate = serial.pin_program(build / 'candidate.so')
producer = build / 'build-comparison.json'
attempt = build / 'build-attempt.json'
source = build / 'source/programs/pump'
script = ROOT / 'scripts/pump_tokenkeg_two_curve_differential.py'
output = PROOF / 'two-curve.json.gz'
inputs = {str(path): digest(path) for path in (candidate, producer, attempt, script)}


def dispatch(selected, destination):
    if hasattr(serial, 'suite_command'):
        return serial.suite_command('tokenkeg_two_curve', script, selected,
                                    destination, source, producer)
    # Baseline driver has no command helper. Execute only its actual command
    # construction statements from the suite loop, then run the real child.
    # This is not a replacement suite runner or a simulated VM execution.
    tree = ast.parse(Path(serial.__file__).read_text(encoding='utf-8'))
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    loop = next(node for node in ast.walk(main) if isinstance(node, ast.For)
                and isinstance(node.target, ast.Tuple)
                and [item.id for item in node.target.elts] == ['name', 'filename'])
    start = next(index for index, node in enumerate(loop.body)
                 if isinstance(node, ast.Assign)
                 and any(isinstance(item, ast.Name) and item.id == 'command' for item in node.targets))
    stop = next(index for index in range(start, len(loop.body))
                if isinstance(loop.body[index], ast.Expr)
                and isinstance(loop.body[index].value, ast.Call)
                and isinstance(loop.body[index].value.func, ast.Attribute)
                and loop.body[index].value.func.attr == 'run')
    statements = ast.Module(body=loop.body[start:stop], type_ignores=[])
    namespace = dict(sys=sys, script=script, candidate=selected, output=destination,
                     args=argparse.Namespace(source_directory=source))
    exec(compile(statements, str(serial.__file__), 'exec'), namespace)
    return namespace['command']


command = dispatch(candidate, output)
code = run('serial-two-curve-dispatch', command)
entry = {'scope': __doc__, 'actual_command': command, 'returncode': code,
         'output_exists': output.is_file(), 'producer_sha256': digest(producer),
         'attempt_sha256': digest(attempt), 'actual_candidate_sha256': digest(candidate),
         'snapshot_has_adjacent_build_report': (candidate.parent / 'build-comparison.json').exists(),
         'real_compiler_build': True, 'full_corpus_executed': False}
(PROOF / 'entry.json').write_text(json.dumps(entry, indent=2) + '\n', encoding='utf-8')
assert inputs == {path: digest(path) for path in inputs}
assert code == 0 and output.is_file(), 'serial dispatch lost the genuine producer receipt after pinning'
result = json.loads(gzip.decompress(output.read_bytes()))
assert result['case_count'] == len(result['cases']) == 20
assert result['verified_outer_signatures'] == 40
assert all(not row['mismatches'] for row in result['cases'])
assert result['candidate_sha256'] == digest(candidate)

negative = PROOF / 'wrong-candidate.json.gz'
wrong = serial.pin_program(ROOT / 'evidence/original/mayhem/deployed.so')
negative_code = run('wrong-candidate', dispatch(wrong, negative))
assert negative_code != 0 and not negative.exists(), 'genuine producer receipt must reject another actual ELF'
assert 'candidate_sha256' in (PROOF / 'wrong-candidate.log').read_text(encoding='utf-8')
summary = dict(entry, matching_cases=20, verified_outer_signatures=40,
               wrong_candidate_returncode=negative_code)
if os.environ.get('SERIAL_FULL_CORPUS') == '1':
    aggregate = PROOF / 'full-serial.json.gz'
    full_code = run('full-serial', [sys.executable, '-B', str(ROOT / 'scripts/pump_validate_all.py'),
                                 '--candidate', str(build / 'candidate.so'),
                                 '--source-directory', str(source), '--output', str(aggregate)], 3600)
    summary.update(full_corpus_executed=True, full_corpus_returncode=full_code)
    (PROOF / 'result.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    assert full_code == 0
    complete = json.loads(gzip.decompress(aggregate.read_bytes()))
    assert complete['case_count'] == 10468 and len(complete['suites']) == 44 and not complete['mismatches']
    summary.update(full_case_count=10468, full_suites=44)
(PROOF / 'result.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
