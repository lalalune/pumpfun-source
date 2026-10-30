"""Run genuine retained ELF audits in a materialized Git-symlink layout.

No scorer/decoder/audit function is patched. Both direct CLIs and the existing
digest-admitted wrapper execute as separate actual Python processes.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

LANE = Path('reconstruction/pump-main/lanes/callgraph-census')
WRAPPER = Path('reconstruction/diagnostics/census-portability/run.py')
DEFAULT_CANDIDATE = Path('research/pump-multihop-sell-fees-20261029/build/candidate/symbols.so.gz')
EXPECTED_CANDIDATE = 'b79428215bac7c4cb487681ea3a5cdad84197fcaa04142a0e68f4a4706008898'
LINK = b'../../evidence/original/pump/deployed.so'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--candidate-gzip', type=Path)
    parser.add_argument('--expect', choices=('before', 'after'), required=True)
    args = parser.parse_args()
    repo, out = args.repo_root.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    staged = out / 'layout'
    closure = [Path('reconstruction/harness') / name for name in (
        'score.py', 'score_admission.py', 'llvm_tools.py', 'original_input.py',
        'elf_symbols.py', 'instruction_stream.py', 'win.py', 'coords.py')]
    closure += [LANE / name for name in (
        'census.py', 'callid_audit.py', 'dataref_audit.py', 'blocksim.py', 'hotness.py')]
    closure += [WRAPPER, Path('reconstruction/base/functions.tsv'), Path('evidence/original/pump/deployed.so')]
    for relative in closure:
        destination = staged / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / relative, destination)
    (staged / 'reconstruction/base/original.so').write_bytes(LINK)
    candidate = out / 'symbols.so'
    archive = args.candidate_gzip or repo / DEFAULT_CANDIDATE
    candidate.write_bytes(gzip.decompress(archive.read_bytes()))
    if args.candidate_gzip is None and sha(candidate) != EXPECTED_CANDIDATE:
        raise ValueError('retained candidate does not match its published packet hash')
    temporary = out / 'temporary'
    temporary.mkdir()
    env = dict(os.environ, TMP=str(temporary), TEMP=str(temporary), PYTHONDONTWRITEBYTECODE='1')
    observations = []

    def invoke(name, command):
        result = subprocess.run([sys.executable, '-I', '-B', '-X', 'utf8', *map(str, command)],
                                cwd=out, env=env, capture_output=True, encoding='utf-8')
        (out / (name + '.stdout')).write_text(result.stdout, encoding='utf-8')
        (out / (name + '.stderr')).write_text(result.stderr, encoding='utf-8')
        return result

    for tool, filename in (('callid', 'callid_audit.py'), ('dataref', 'dataref_audit.py')):
        direct_output, wrapper_output = out / (tool + '-direct.json'), out / (tool + '-wrapper.json')
        common = ['--cand', candidate, '--json']
        direct = invoke(tool + '-direct', [staged / LANE / filename, *common, direct_output])
        wrapped = invoke(tool + '-wrapper', [staged / WRAPPER, tool, *common, wrapper_output])
        if wrapped.returncode != 0:
            raise RuntimeError('existing wrapper control failed: ' + wrapped.stderr)
        if args.expect == 'before':
            if direct.returncode == 0 or direct_output.exists() or 'expected ELF64 little-endian version 1' not in direct.stderr:
                raise AssertionError('did not reproduce the original-input failure')
        elif direct.returncode != 0 or direct_output.read_bytes() != wrapper_output.read_bytes():
            raise AssertionError('direct audit does not reproduce the wrapper control exactly')
        data = json.loads(wrapper_output.read_text(encoding='utf-8'))
        canonical = dict(data)
        # The two standalone invocations deliberately use different output
        # directories. Exclude only their explicit candidate pathname when
        # comparing before/after diagnostic contents; all findings remain.
        canonical.pop('candidate')
        canonical_sha256 = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
        summary = ({key: data[key] for key in ('rounds', 'normalized_matched', 'bisimilar_matched')}
                   if tool == 'callid' else {key: data[key] for key in ('width', 'clean', 'flagged')})
        observations.append({'tool': tool, 'direct_returncode': direct.returncode,
                             'direct_report_exists': direct_output.exists(), 'wrapper_returncode': wrapped.returncode,
                             'wrapper_report_sha256': sha(wrapper_output),
                             'diagnostic_content_sha256': canonical_sha256,
                             'direct_equals_wrapper': direct_output.exists() and direct_output.read_bytes() == wrapper_output.read_bytes(),
                             'summary': summary})
    # Same exact Git link bytes supplied as a candidate must not be resolved.
    candidate_link = out / 'candidate-link.so'
    candidate_link.write_bytes(LINK)
    negative = invoke('candidate-link-negative', [staged / WRAPPER, 'callid', '--cand', candidate_link,
                                                '--json', out / 'candidate-link-negative.json'])
    if negative.returncode == 0 or (out / 'candidate-link-negative.json').exists():
        raise AssertionError('a non-ELF candidate was admitted')
    if (staged / 'reconstruction/base/original.so').read_bytes() != LINK:
        raise AssertionError('materialized Git link was changed')
    result = {'expect': args.expect, 'original_sha256': sha(staged / 'evidence/original/pump/deployed.so'),
              'inventory_sha256': sha(staged / 'reconstruction/base/functions.tsv'),
              'candidate_sha256': sha(candidate), 'archive_sha256': sha(archive),
              'source_sha256': {path.as_posix(): sha(staged / path) for path in closure if path.suffix == '.py'},
              'audits': observations, 'candidate_link_negative_returncode': negative.returncode,
              'limits': 'Retained compiler-built historical candidate; static call/data diagnostics only. No new compiler or VM execution, source reconstruction gain or security approval.'}
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'expect': args.expect, 'candidate_sha256': result['candidate_sha256'], 'audits': observations}))


if __name__ == '__main__':
    main()
