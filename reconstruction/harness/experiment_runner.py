#!/usr/bin/env python3
"""Bounded, resumable local experiments. Commands are argv arrays, never shell text."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import uuid

# Generated directories are never source, but only the experiment root's
# target directory is generated build output: nested target directories can
# contain source, mirroring source_inputs and build_source_manifest.
ALWAYS_IGNORED = ('.git', '__pycache__')


def stage_ignore(source):
    """copytree ignore matching manifest(): target only at the source root."""
    source = Path(source)

    def ignore(directory, names):
        ignored = [name for name in names if name in ALWAYS_IGNORED]
        if Path(directory) == source and 'target' in names:
            ignored.append('target')
        return ignored

    return ignore


def digest(data): return hashlib.sha256(data).hexdigest()


def manifest(source):
    source = Path(source)
    if not source.is_dir() or source.is_symlink():
        raise ValueError('source must be a real directory')
    result = {}
    for directory, dirs, files in os.walk(source):
        dirs[:] = sorted(d for d in dirs if d not in ALWAYS_IGNORED)
        # Validate directory links before the root-target exclusion, so a
        # symlinked root target is rejected instead of silently skipped.
        for name in dirs:
            if (Path(directory) / name).is_symlink():
                raise ValueError('source symlinks are unsupported')
        if Path(directory) == source:
            dirs[:] = [d for d in dirs if d != 'target']
        for name in dirs + sorted(files):
            path = Path(directory) / name
            if path.is_symlink(): raise ValueError('source symlinks are unsupported')
            if path.is_file():
                result[path.relative_to(source).as_posix()] = {'sha256': digest(path.read_bytes()),
                                                             'executable': bool(path.stat().st_mode & 0o111)}
            elif not path.is_dir(): raise ValueError('special source files are unsupported')
    return result


def input_hashes(inputs):
    result = {}
    for value in inputs:
        path = Path(value).resolve(strict=True)
        if not path.is_file(): raise ValueError('declared input must be a file')
        result[str(path)] = digest(path.read_bytes())
    return result


def identity(source, command, inputs, timeout):
    if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
        raise ValueError('command must be a nonempty argv array')
    if not isinstance(timeout, (int, float)) or not 0 < timeout <= 86400:
        raise ValueError('timeout must be positive and at most one day')
    executable = shutil.which(command[0])
    if executable is None: raise ValueError('command executable is unavailable')
    return {'schema': 'experiment-input-v1', 'source': manifest(source), 'command': command,
            'inputs': input_hashes([executable, *inputs]), 'timeout': timeout,
            'environment_sha256': digest(json.dumps(dict(os.environ), sort_keys=True).encode()),
            'runner_sha256': digest(Path(__file__).read_bytes())}


def atomic_json(path, value):
    fd, temporary = tempfile.mkstemp(prefix='.receipt-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, indent=2); stream.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def artifacts(attempt):
    result = {}
    for path in [attempt / 'stdout.log', attempt / 'stderr.log', *sorted((attempt / 'output').rglob('*'))]:
        if path.is_symlink(): raise ValueError('output symlinks are unsupported')
        if path.is_file(): result[path.relative_to(attempt).as_posix()] = digest(path.read_bytes())
        elif not path.is_dir(): raise ValueError('special output files are unsupported')
    return result


def run_trial(source, command, destination, inputs=(), timeout=300):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination == source or source in destination.parents or destination in source.parents:
        raise ValueError('source and destination must be separate trees')
    admission = identity(source, command, inputs, timeout)
    key = digest(json.dumps(admission, sort_keys=True).encode())
    destination.mkdir(parents=True, exist_ok=True)
    with (destination / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        receipt_path = destination / 'latest.json'
        if receipt_path.exists():
            previous = json.loads(receipt_path.read_text())
            name = previous.get('attempt', '')
            if not isinstance(name, str) or not name.startswith('attempt-') or Path(name).name != name:
                raise ValueError('invalid retained attempt path')
            attempt = destination / name
            if previous.get('key') == key and previous.get('status') in ('pass', 'fail'):
                try:
                    valid = not attempt.is_symlink() and artifacts(attempt) == previous['artifacts']
                except (OSError, ValueError): valid = False
                if valid: return dict(previous, reused=True)
        attempt = destination / ('attempt-' + uuid.uuid4().hex)
        attempt.mkdir()
        copied, work, output = (attempt / x for x in ('source', 'work', 'output'))
        shutil.copytree(source, copied, ignore=stage_ignore(source))
        if manifest(copied) != admission['source'] or manifest(source) != admission['source']:
            raise ValueError('source changed while copying')
        work.mkdir(); output.mkdir()
        replacements = {'{source}': str(copied), '{work}': str(work), '{out}': str(output)}
        argv = []
        for arg in command:
            for token, value in replacements.items(): arg = arg.replace(token, value)
            argv.append(arg)
        argv[0] = str(Path(shutil.which(command[0])).resolve())
        status, reason, code = 'error', None, None
        with (attempt / 'stdout.log').open('wb') as stdout, (attempt / 'stderr.log').open('wb') as stderr:
            process = subprocess.Popen(argv, cwd=work, stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                code = process.wait(timeout=timeout)
                status = 'pass' if code == 0 else 'fail' if code == 1 else 'error'
            except subprocess.TimeoutExpired:
                reason = 'timeout'
            finally:
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                process.wait()
        if manifest(source) != admission['source'] or manifest(copied) != admission['source'] or input_hashes(admission['inputs']) != admission['inputs']:
            status, reason = 'error', 'source or declared input changed during execution'
        record = {'schema': 'experiment-result-v1', 'key': key, 'attempt': attempt.name,
                  'status': status, 'reason': reason, 'returncode': code, 'inputs': admission,
                  'artifacts': artifacts(attempt), 'reused': False}
        atomic_json(receipt_path, record)
        return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('matrix', type=Path, help='JSON: list of {name, source, command, inputs?, timeout?}')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--max-trials', type=int, default=20)
    args = parser.parse_args()
    rows = json.loads(args.matrix.read_text())
    if not isinstance(rows, list) or not rows or not 0 < len(rows) <= args.max_trials:
        parser.error('matrix must be nonempty and within --max-trials')
    names = set()
    for row in rows:
        name = row.get('name', '')
        if not isinstance(name, str) or not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name) or name in names:
            parser.error('trial names must be unique simple identifiers')
        names.add(name)
        identity(row['source'], row['command'], row.get('inputs', []), row.get('timeout', 300))
    results = {row['name']: run_trial(row['source'], row['command'], args.out / row['name'], row.get('inputs', []), row.get('timeout', 300)) for row in rows}
    print(json.dumps(results, indent=2))
    return 2 if any(r['status'] == 'error' for r in results.values()) else 0


if __name__ == '__main__': raise SystemExit(main())
