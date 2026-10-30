#!/usr/bin/env python3
"""Locate a first-parent match regression using the experiment command contract."""
import argparse
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
from experiment_runner import run_trial, atomic_json


def narrow(revisions, evaluate, budget):
    if len(revisions) < 2 or budget < 2: raise ValueError('need two revisions and at least two trials')
    seen = {}
    def check(index):
        if index not in seen:
            if len(seen) >= budget: return None
            status = evaluate(revisions[index])
            if status not in ('pass', 'fail', 'error'): raise ValueError('invalid oracle status')
            seen[index] = status
        return seen[index]
    low, high = 0, len(revisions) - 1
    good_status, bad_status = check(low), check(high)
    if good_status != 'pass' or bad_status != 'fail':
        return {'status': 'invalid-endpoints', 'tested': {revisions[i]: s for i, s in seen.items()}}
    while high - low > 1:
        choices = [i for i in range(low + 1, high) if i not in seen]
        if not choices or len(seen) >= budget: break
        middle = min(choices, key=lambda i: (abs(i - (low + high) / 2), i))
        status = check(middle)
        if status == 'pass': low = middle
        elif status == 'fail': high = middle
    return {'status': 'boundary-found' if high - low == 1 else 'unresolved',
            'last_passing': revisions[low], 'first_failing_bound': revisions[high],
            'possible_first_failures': revisions[low + 1:high + 1],
            'tested': {revisions[i]: s for i, s in sorted(seen.items())},
            'assumption': 'A monotonic pass-to-fail transition on the supplied first-parent history.'}


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def revision_chain(repo, good, bad):
    if good.startswith('-') or bad.startswith('-'): raise ValueError('invalid revision')
    good_sha = git(repo, 'rev-parse', '--verify', good + '^{commit}').decode().strip()
    bad_sha = git(repo, 'rev-parse', '--verify', bad + '^{commit}').decode().strip()
    history = git(repo, 'rev-list', '--first-parent', bad_sha).decode().splitlines()
    if good_sha not in history: raise ValueError('good revision must be on bad revision first-parent history')
    return list(reversed(history[:history.index(good_sha) + 1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--good', required=True); parser.add_argument('--bad', required=True)
    parser.add_argument('--source-subdir', default='programs/pump')
    parser.add_argument('--oracle', type=Path, required=True, help='JSON {command, inputs?, timeout?}')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--max-trials', type=int, default=20)
    args = parser.parse_args()
    subdir = Path(args.source_subdir)
    if subdir.is_absolute() or '..' in subdir.parts: parser.error('source subdirectory must stay inside repository')
    revisions = revision_chain(args.repo, args.good, args.bad)
    config = json.loads(args.oracle.read_text())
    args.out.mkdir(parents=True, exist_ok=True)
    def evaluate(revision):
        with tempfile.TemporaryDirectory(prefix='bisect-source-', dir=args.out) as temporary:
            blob = git(args.repo, 'archive', revision, '--', subdir.as_posix())
            with tarfile.open(fileobj=io.BytesIO(blob)) as archive:
                if any(m.issym() or m.islnk() for m in archive.getmembers()): raise ValueError('source links unsupported')
                archive.extractall(temporary, filter='data')
            return run_trial(Path(temporary) / subdir, config['command'], args.out / 'trials' / revision,
                             config.get('inputs', []), config.get('timeout', 300))['status']
    result = narrow(revisions, evaluate, args.max_trials)
    atomic_json(args.out / 'bisect.json', result)
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'boundary-found' else 2


if __name__ == '__main__': raise SystemExit(main())
