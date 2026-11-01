#!/usr/bin/env python3
"""Bounded, resumable local experiments. Commands are argv arrays, never shell text."""
import argparse
import fcntl
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import signal
import stat
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
        if Path(directory) == source and 'target' in names and (source / 'target').is_dir():
            ignored.append('target')
        return ignored

    return ignore


def digest(data): return hashlib.sha256(data).hexdigest()


# A long-lived importer keeps executing this loaded module if its source file
# changes on disk. Retain the import-time source fingerprint instead of
# relabeling the import with a later source-file read.
LOADED_RUNNER_SHA256 = digest(Path(__file__).read_bytes())


def linked_source(path):
    metadata = path.lstat()
    return (stat.S_ISLNK(metadata.st_mode) or
            bool(getattr(metadata, 'st_file_attributes', 0) &
                 getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)))


def manifest(source):
    source = Path(source)
    if not source.is_dir() or linked_source(source):
        raise ValueError('source must be a real directory')
    result = {}
    def traversal_error(error):
        raise error
    for directory, dirs, files in os.walk(source, onerror=traversal_error):
        dirs[:] = sorted(d for d in dirs if d not in ALWAYS_IGNORED)
        # Validate directory links before the root-target exclusion, so a
        # symlinked root target is rejected instead of silently skipped.
        for name in dirs:
            if (Path(directory) / name).is_symlink():
                raise ValueError('source symlinks are unsupported')
        if Path(directory) == source:
            dirs[:] = [d for d in dirs if d != 'target']
        # Nonempty directory membership follows from its files/descendants.
        # Empty leaves are also observable by build scripts and experiment commands.
        if Path(directory) != source and not dirs and not any(name not in ALWAYS_IGNORED for name in files):
            result[Path(directory).relative_to(source).as_posix() + '/'] = {'directory': True}
        # A linked worktree or submodule stores .git as a file; staging omits it too.
        for name in dirs + sorted(name for name in files if name not in ALWAYS_IGNORED):
            path = Path(directory) / name
            if linked_source(path): raise ValueError('linked source inputs are unsupported')
            if path.is_file():
                result[path.relative_to(source).as_posix()] = {'sha256': digest(path.read_bytes()),
                                                             'executable': bool(path.stat().st_mode & 0o111),
                                                             'execute_bits': path.stat().st_mode & 0o111}
            elif not path.is_dir(): raise ValueError('special source files are unsupported')
    return result


def input_hashes(inputs):
    result = {}
    for value in inputs:
        path = Path(value).resolve(strict=True)
        if not path.is_file(): raise ValueError('declared input must be a file')
        result[str(path)] = digest(path.read_bytes())
    return result


def input_execute_bits(inputs):
    return {path: Path(path).stat().st_mode & 0o111 for path in inputs}


def identity(source, command, inputs, timeout, *, environment=None):
    if not isinstance(command, list):
        raise ValueError('command must be a nonempty argv array')
    command = list(command)
    if not command or not all(isinstance(x, str) and x for x in command):
        raise ValueError('command must be a nonempty argv array')
    # exec cannot carry these, and fsencode refuses the rest; find out before any trial runs.
    if any(b'\0' in os.fsencode(x) for x in command):
        raise ValueError('command arguments must not contain NUL')
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 86400:
        raise ValueError('timeout must be positive and at most one day')
    environment = dict(os.environ if environment is None else environment)
    declared = shutil.which(command[0], path=environment.get('PATH', os.defpath))
    if declared is None: raise ValueError('command executable is unavailable')
    executable = Path(declared).resolve(strict=True)
    inputs = list(inputs)
    declared_paths = {os.path.abspath(value): str(Path(value).resolve(strict=True))
                      for value in inputs}
    hashes = input_hashes([executable, *inputs])
    return {'schema': 'experiment-input-v1', 'source': manifest(source), 'command': command,
            'executable': str(executable), 'invocation': os.path.abspath(declared),
            'inputs': hashes, 'input_execute_bits': input_execute_bits(hashes), 'timeout': timeout,
            'declared_input_paths': declared_paths,
            'environment_sha256': digest(json.dumps(environment, sort_keys=True).encode()),
            'runner_sha256': LOADED_RUNNER_SHA256}


def admitted_inputs_match(admission):
    return (input_hashes(admission['inputs']) == admission['inputs']
            and input_execute_bits(admission['inputs']) == admission['input_execute_bits']
            and all(str(Path(path).resolve(strict=True)) == target
                    for path, target in admission['declared_input_paths'].items()))


def atomic_json(path, value):
    fd, temporary = tempfile.mkstemp(prefix='.receipt-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, indent=2); stream.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def output_paths(root):
    def traversal_error(error):
        raise error
    for directory, dirs, files in os.walk(root, onerror=traversal_error, followlinks=False):
        for name in dirs:
            if linked_source(Path(directory) / name):
                raise ValueError('linked output directories are unsupported')
        for name in dirs + files:
            yield Path(directory) / name


def artifacts(attempt):
    output = attempt / 'output'
    if not output.is_dir() or linked_source(output):
        raise ValueError('retained output must be a real directory')
    result = {}
    for path in [attempt / 'stdout.log', attempt / 'stderr.log', *sorted(output_paths(output))]:
        if linked_source(path): raise ValueError('output symlinks and other linked output files are unsupported')
        if path.is_file():
            result[path.relative_to(attempt).as_posix()] = {
                'sha256': digest(path.read_bytes()),
                'executable': bool(path.stat().st_mode & 0o111),
                'execute_bits': path.stat().st_mode & 0o111}
        elif path.is_dir():
            result[path.relative_to(attempt).as_posix() + '/'] = {'directory': True}
        else: raise ValueError('special output files are unsupported')
    return result


def separate_trees(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination == source or source in destination.parents or destination in source.parents:
        raise ValueError('source and destination must be separate trees')
    # resolve() removes symlinks but can preserve alternate case spellings on
    # case-insensitive volumes. Compare existing ancestors by filesystem identity
    # as well; the destination itself may not have been created yet.
    for root, descendant in ((source, destination), (destination, source)):
        try:
            root_info = root.stat()
        except FileNotFoundError:
            continue
        for path in (descendant, *descendant.parents):
            try:
                info = path.stat()
            except FileNotFoundError:
                continue
            if os.path.samestat(root_info, info):
                raise ValueError('source and destination must be separate trees')
    return source, destination


def paths_alias(first, second):
    """Include existing physical aliases without dropping absent-path checks."""
    first, second = Path(first).resolve(), Path(second).resolve()
    if first == second:
        return True
    try:
        return first.samefile(second)
    except FileNotFoundError:
        return False


def check_receipt_inputs(destination, inputs):
    receipt_path = Path(destination) / 'latest.json'
    if any(paths_alias(receipt_path, path) for path in inputs):
        raise ValueError('trial receipt overlaps a declared input')
    return receipt_path


def reusable_result(record, admission, key):
    """Require saved labels and provenance to describe this completed result."""
    status = record.get('status')
    code = record.get('returncode')
    inputs = record.get('inputs')
    return (record.get('schema') == 'experiment-result-v1'
            and record.get('key') == key and status in ('pass', 'fail')
            and type(code) is int and code == (0 if status == 'pass' else 1)
            and record.get('reason') is None and inputs == admission
            # Dict equality alone treats False/0 and integer/float as equal.
            and digest(json.dumps(inputs, sort_keys=True).encode()) == key)


def run_trial(source, command, destination, inputs=(), timeout=300):
    source, destination = separate_trees(source, destination)
    environment = dict(os.environ)
    admission = identity(source, command, inputs, timeout, environment=environment)
    receipt_path = check_receipt_inputs(destination, admission['inputs'])
    key = digest(json.dumps(admission, sort_keys=True).encode())
    destination.mkdir(parents=True, exist_ok=True)
    with (destination / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        # Refresh source and declared file contents/modes after waiting. Keep the admitted
        # executable and alias targets: re-resolving them could silently run a
        # different command. Their original bindings are rechecked before launch.
        refresh = [path for path in admission['inputs'] if path != admission['executable']]
        admission = dict(admission, source=manifest(source),
                         inputs={**admission['inputs'], **input_hashes(refresh)},
                         input_execute_bits={**admission['input_execute_bits'],
                                             **input_execute_bits(refresh)})
        key = digest(json.dumps(admission, sort_keys=True).encode())
        if receipt_path.exists():
            previous = json.loads(receipt_path.read_text())
            name = previous.get('attempt', '')
            if not isinstance(name, str) or not name.startswith('attempt-') or Path(name).name != name:
                raise ValueError('invalid retained attempt path')
            attempt = destination / name
            if reusable_result(previous, admission, key):
                try:
                    valid = (admitted_inputs_match(admission)
                             and not attempt.is_symlink()
                             and manifest(attempt / 'source') == admission['source']
                             and artifacts(attempt) == previous['artifacts'])
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
        for arg in admission['command']:
            argv.append(re.sub(r'\{(?:source|work|out)\}',
                               lambda match: replacements[match.group()], arg))
        # Preserve argv[0] for virtual environments/rustup, but do not resolve
        # the alias again: it may now point somewhere other than the hashed tool.
        argv[0] = admission['invocation']
        status, reason, code = 'error', None, None
        with (attempt / 'stdout.log').open('wb') as stdout, (attempt / 'stderr.log').open('wb') as stderr:
            try:
                if not admitted_inputs_match(admission):
                    raise OSError('declared input changed before launch')
                process = subprocess.Popen(argv, executable=admission['executable'], cwd=work,
                                           stdout=stdout, stderr=stderr, start_new_session=True,
                                           env=environment)
            except OSError as error:
                reason = 'process start failed'
                stderr.write((str(error) + '\n').encode('utf-8', errors='replace'))
            else:
                try:
                    code = process.wait(timeout=timeout)
                    status = 'pass' if code == 0 else 'fail' if code == 1 else 'error'
                except subprocess.TimeoutExpired:
                    reason = 'timeout'
                finally:
                    try: os.killpg(process.pid, signal.SIGKILL)
                    # As in build_process: the session may already be gone.
                    except (ProcessLookupError, PermissionError): pass
                    process.wait()
        retained = {}
        try:
            if manifest(source) != admission['source'] or manifest(copied) != admission['source'] or not admitted_inputs_match(admission):
                status, reason = 'error', 'source or declared input changed during execution'
            retained = artifacts(attempt)
        except (OSError, ValueError) as error:
            # The attempt ran, so its logs and receipt must outlive a failed check.
            status, reason = 'error', f'post-run validation failed: {error}'
        record = {'schema': 'experiment-result-v1', 'key': key, 'attempt': attempt.name,
                  'status': status, 'reason': reason, 'returncode': code, 'inputs': admission,
                  'artifacts': retained, 'reused': False}
        atomic_json(receipt_path, record)
        return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('matrix', type=Path, help='JSON: list of {name, source, command, inputs?, timeout?}')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--max-trials', type=int, default=20)
    args = parser.parse_args()
    try:
        rows = json.loads(args.matrix.read_text(encoding='utf-8'))
        if not isinstance(rows, list) or not rows or not 0 < len(rows) <= args.max_trials:
            raise ValueError('matrix must be nonempty and within --max-trials')
        names = set()
        admissions = []
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError('each trial must be an object')
            name = row.get('name', '')
            # Each name is an output directory, and macOS volumes fold case by default.
            if not isinstance(name, str) or not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name) or name.casefold() in names:
                raise ValueError('trial names must be unique simple identifiers')
            if not isinstance(row.get('inputs', []), list):
                raise ValueError('trial inputs must be an array of file paths')
            names.add(name.casefold())
            admissions.append(identity(row['source'], row['command'], row.get('inputs', []), row.get('timeout', 300)))
        # Admit the entire matrix before the first command, including cross-row inputs.
        for row in rows:
            for other, admission in zip(rows, admissions):
                separate_trees(other['source'], args.out / row['name'])
                check_receipt_inputs(args.out / row['name'], admission['inputs'])
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.error(f'invalid experiment matrix: {error}')
    results = {row['name']: run_trial(row['source'], row['command'], args.out / row['name'], row.get('inputs', []), row.get('timeout', 300)) for row in rows}
    print(json.dumps(results, indent=2))
    return 2 if any(r['status'] == 'error' for r in results.values()) else 0


if __name__ == '__main__': raise SystemExit(main())
