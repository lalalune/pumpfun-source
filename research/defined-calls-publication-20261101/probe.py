"""Real static diagnostic CLI publication, with a bounded OS write failure."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import tempfile

GENERATOR = 'reconstruction/diagnostics/defined-dynamic-calls/generate.py'
SOURCES = (GENERATOR, 'scripts/reconstruction_roadmap.py', 'scripts/window_elf_reader.py',
           'scripts/deep_disassembly.py', 'research/tooling-roadmap-call-classification-20261029/proof.py',
           'research/tooling-roadmap-call-classification-20261029/archived/reconstruction_roadmap.py')
CAPTURES = tuple('evidence/original/' + name + '/deployed.so' for name in ('pump', 'pump_amm', 'mayhem'))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def limited():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
    resource.setrlimit(resource.RLIMIT_FSIZE, (64, 64))


def inventory(root):
    if not root.is_dir():
        return None
    return {p.relative_to(root).as_posix(): {'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}
            for p in sorted(root.rglob('*')) if p.is_file()}


def run(repo, revision=None):
    def source(name):
        return (subprocess.check_output(['git', '-C', str(repo), 'show', revision + ':' + name])
                if revision else (repo / name).read_bytes())
    sources = {name: source(name) for name in SOURCES}
    captures = {name: (repo / name).read_bytes() for name in CAPTURES}
    results = {'source_sha256': {k: sha(v) for k, v in sources.items()},
               'capture_sha256': {k: sha(v) for k, v in captures.items()}, 'cases': {}}
    with tempfile.TemporaryDirectory(prefix='defined-calls-publication-proof-') as temporary:
        root = Path(temporary).resolve()
        cohort = root / 'repo'
        for name, raw in {**sources, **captures}.items():
            path = cohort / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        entrypoint = cohort / GENERATOR

        def cli(name, output, limit=False, late=False):
            command = [sys.executable, '-B', str(entrypoint), '--repo', str(cohort), '--output', str(output)]
            marker = root / 'late-observer.txt'
            if late:
                observer = '''import pathlib,runpy,sys
entry,repo,output,marker=sys.argv[1:]
def trace(frame,event,arg):
 if event=='return' and frame.f_code.co_name=='generate_roadmap' and frame.f_code.co_filename==str(pathlib.Path(repo)/'scripts/reconstruction_roadmap.py'):
  sys.setprofile(None)
  path=pathlib.Path(output)
  if not path.exists():
   path.mkdir();pathlib.Path(marker).write_text('created')
 return trace
sys.setprofile(trace)
sys.argv=[entry,'--repo',repo,'--output',output]
runpy.run_path(entry,run_name='__main__')
'''
                command = [sys.executable, '-B', '-c', observer, str(entrypoint), str(cohort), str(output), str(marker)]
            completed = subprocess.run(command, capture_output=True, text=True,
                                       timeout=90, preexec_fn=limited if limit else None)
            result = {'returncode': completed.returncode, 'output_exists': output.exists(),
                      'output_symlink': output.is_symlink(), 'files': inventory(output),
                      'file_size_error': 'File too large' in completed.stderr,
                      'staging_leftovers': [p.name for p in output.parent.iterdir()
                                           if p.name.startswith('.' + output.name[:32])],
                      'stderr_tail': completed.stderr.replace(str(root), 'OWNED')[-1000:]}
            if late:
                result['late_destination_created'] = marker.exists()
                result['late_destination_empty'] = output.is_dir() and not any(output.iterdir())
            if completed.returncode == 0:
                manifest = json.loads((output / 'manifest.json').read_bytes())
                assert all(sha((output / file).read_bytes()) == digest for file, digest in manifest.items())
                check = subprocess.run([sys.executable, '-I', '-B', str(output / 'verify.py')],
                                       capture_output=True, text=True, timeout=30)
                result['generated_verifier_exit'] = check.returncode
                assert check.returncode == 0, check.stdout + check.stderr
                if name == 'normal':
                    results['normal_bindings'] = json.loads((output / 'dynamic-call-inputs.json').read_bytes())
            results['cases'][name] = result
            return result

        normal = cli('normal', root / 'normal')
        assert normal['returncode'] == 0, normal
        for name in ('a' * 240, '\uacb0' * 80):
            cli('long_' + ('ascii' if name.isascii() else 'unicode'), root / name)
        parent = root / 'real-parent'
        parent.mkdir()
        alias = root / 'parent-alias'
        alias.symlink_to(parent, target_is_directory=True)
        cli('parent_alias', alias / 'packet')
        output = root / 'failed'
        cli('limited', output, True)
        cli('same_destination_retry', output)
        output = root / 'dangling'
        target = root / 'dangling-target'
        output.symlink_to(target, target_is_directory=True)
        cli('dangling_link', output)
        results['cases']['dangling_link']['target_exists'] = target.exists()
        for name, populated in [('existing_empty', False), ('existing_populated', True)]:
            output = root / name
            output.mkdir()
            if populated:
                (output / 'owned.txt').write_bytes(b'prior result\n')
            before = inventory(output)
            cli(name, output)
            results['cases'][name]['prior_preserved'] = before == inventory(output)
        cli('late_destination', root / 'late', late=True)
        assert all((cohort / name).read_bytes() == raw for name, raw in {**sources, **captures}.items())
        results['inputs_preserved'] = True
    return results


def validate(result, expect):
    cases = result['cases']
    fixed = expect == 'fixed'
    for name in ('normal', 'long_ascii', 'long_unicode', 'parent_alias'):
        assert cases[name]['returncode'] == 0, name
        assert cases[name]['generated_verifier_exit'] == 0, name
        assert cases[name]['files'] == cases['normal']['files'], name
    failed = cases['limited']
    assert failed['returncode'] != 0 and failed['file_size_error']
    assert failed['output_exists'] == (not fixed)
    assert (cases['same_destination_retry']['returncode'] == 0) == fixed
    link = cases['dangling_link']
    assert link['output_symlink'] and link['target_exists'] == (not fixed)
    assert (link['returncode'] == 0) == (not fixed)
    for name in ('existing_empty', 'existing_populated'):
        assert cases[name]['returncode'] != 0 and cases[name]['prior_preserved']
    late = cases['late_destination']
    assert late['late_destination_created'] == fixed
    assert (late['returncode'] != 0 and late['late_destination_empty']) == fixed
    assert all(not row['staging_leftovers'] for row in cases.values())
    assert result['inputs_preserved']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--revision')
    parser.add_argument('--expect', choices=('base', 'fixed'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.repo.resolve(), args.revision)
    validate(result, args.expect)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({name: {k: v for k, v in row.items() if k not in ('files', 'stderr_tail')}
                      for name, row in result['cases'].items()}, indent=2))
