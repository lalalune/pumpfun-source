"""Replay explicit regex selection against a genuine retained symbolized ELF."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ARCHIVE = 'research/pump-multihop-token-quote-20261029/build/parent/symbols.so.gz'
CANDIDATE_SHA256 = 'e1c9bdc3b248d41ebd73c1f8d0d2756edf95eafa178b8aed4a8ae0715649705a'
MODULES = ('win', 'score', 'score_admission', 'llvm_tools', 'original_input',
           'elf_symbols', 'instruction_stream', 'target_metric', 'compare_scores')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def collect(repo, objdump, revision=None, expected='fixed'):
    repo, objdump = Path(repo).resolve(), Path(objdump).resolve()
    names = ['reconstruction/harness/' + name + '.py' for name in MODULES]
    sources = {name: subprocess.check_output(['git', '-C', str(repo), 'show', revision + ':' + name])
               if revision else (repo / name).read_bytes() for name in names}
    inputs = {name: (repo / name).read_bytes() for name in (
        ARCHIVE, 'evidence/original/pump/deployed.so', 'reconstruction/base/functions.tsv')}
    candidate = gzip.decompress(inputs[ARCHIVE])
    require(sha(candidate) == CANDIDATE_SHA256, 'retained candidate changed')
    tool_bytes = objdump.read_bytes()
    env = dict(os.environ, PUMP_OBJDUMP=str(objdump))
    result = {'source_sha256': {name: sha(data) for name, data in sources.items()},
              'input_sha256': {name: sha(data) for name, data in inputs.items()},
              'candidate_sha256': sha(candidate), 'objdump_sha256': sha(tool_bytes), 'cases': {}}
    specifications = (
        ('show_absent', 'win', ['show', '0x120'], 0),
        ('show_empty', 'win', ['show', '0x120', '--sym', ''], 0),
        ('show_equivalent', 'win', ['show', '0x120', '--sym', '(?:)'], 0),
        ('show_restrictive', 'win', ['show', '0x120', '--sym', '^custom_panic$'], 0),
        ('show_no_match', 'win', ['show', '0x120', '--sym', '^no_such_retained_function$'], 1),
        ('show_invalid', 'win', ['show', '0x120', '--sym', '['], 2),
        ('sym_empty', 'win', ['sym', ''], 0),
        ('sym_equivalent', 'win', ['sym', '(?:)'], 0),
        ('metric_empty', 'target_metric', ['0x120', '--sym', ''], 0),
        ('metric_equivalent', 'target_metric', ['0x120', '--sym', '(?:)'], 0),
    )
    with tempfile.TemporaryDirectory(prefix='window-empty-regex-') as temporary:
        root = Path(temporary)
        for name, data in sources.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        base = root / 'reconstruction/base'
        base.mkdir()
        (base / 'original.so').write_bytes(inputs['evidence/original/pump/deployed.so'])
        (base / 'functions.tsv').write_bytes(inputs['reconstruction/base/functions.tsv'])
        image = root / 'retained-symbols.so'
        image.write_bytes(candidate)
        outputs = {}
        for label, module, arguments, exit_code in specifications:
            command = [sys.executable, '-I', '-B', str(root / 'reconstruction/harness' / (module + '.py'))]
            command += arguments + ['--cand', str(image)] if module == 'win' else [str(image), *arguments]
            run = subprocess.run(command, cwd=root, env=env, capture_output=True, timeout=90)
            require(run.returncode == exit_code, label + ': ' + run.stderr.decode('utf-8', errors='replace'))
            stdout = run.stdout.decode('utf-8')
            lines = stdout.splitlines()
            count = sum(line.startswith('  cand ') for line in lines) if label.startswith('show_') else len(lines)
            outputs[label] = run.stdout
            result['cases'][label] = {'exit_code': run.returncode, 'candidate_rows': count,
                'stdout_sha256': sha(run.stdout), 'stderr_sha256': sha(run.stderr),
                'selected_diff': next((line for line in lines if line.startswith('--- diff')), None)}
        require(result['cases']['show_absent']['candidate_rows'] == 3, 'absent filter behavior changed')
        require(result['cases']['show_restrictive']['candidate_rows'] == 1, 'restrictive filter changed')
        require(result['cases']['show_equivalent']['candidate_rows'] == 1090, 'retained function count changed')
        require(outputs['sym_empty'] == outputs['sym_equivalent'], 'symbol listing regex equivalence failed')
        require(outputs['metric_empty'] == outputs['metric_equivalent'], 'target metric regex equivalence failed')
        for label in ('sym_empty', 'metric_empty'):
            require(result['cases'][label]['candidate_rows'] == 1090, label + ' inventory differs')
        equivalent = 'show_equivalent' if expected == 'fixed' else 'show_absent'
        require(outputs['show_empty'] == outputs[equivalent], 'explicit empty filter used the wrong scope')
        require(result['cases']['show_empty']['selected_diff'] == result['cases']['show_equivalent']['selected_diff'],
                'the selected body changed in this retained witness')
        require(image.read_bytes() == candidate, 'owned candidate changed')
        require((base / 'original.so').read_bytes() == inputs['evidence/original/pump/deployed.so'], 'owned original changed')
        require((base / 'functions.tsv').read_bytes() == inputs['reconstruction/base/functions.tsv'], 'owned inventory changed')
        require(all((root / name).read_bytes() == data for name, data in sources.items()), 'owned helpers changed')
    require(all((repo / name).read_bytes() == data for name, data in inputs.items()), 'retained inputs changed')
    require(objdump.read_bytes() == tool_bytes, 'objdump changed')
    result.update(actual_cli_calls=len(specifications), retained_inputs_preserved=True,
                  objdump_preserved=True, selected_top_body_unchanged=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--objdump', type=Path, required=True)
    parser.add_argument('--revision')
    parser.add_argument('--expect', choices=('base', 'fixed'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = collect(args.repo, args.objdump, args.revision, args.expect)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({name: row['candidate_rows'] for name, row in result['cases'].items()}))


if __name__ == '__main__':
    main()
