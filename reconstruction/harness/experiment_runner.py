#!/usr/bin/env python3
"""Bounded, resumable local experiments. Commands are argv arrays, never shell text."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import time
import uuid

SUPERVISOR_PATH = Path(__file__).resolve().with_name('process_supervisor.py')
SUPERVISOR_BYTES = SUPERVISOR_PATH.read_bytes()
SUPERVISOR_SPEC = importlib.util.spec_from_file_location('_experiment_process_supervisor',
                                                        SUPERVISOR_PATH)
if SUPERVISOR_SPEC is None or SUPERVISOR_SPEC.loader is None:
    raise ImportError(f'cannot load process supervisor from {SUPERVISOR_PATH}')
SUPERVISOR = importlib.util.module_from_spec(SUPERVISOR_SPEC)
SUPERVISOR.__dict__['_ADMITTED_SOURCE_BYTES'] = SUPERVISOR_BYTES
exec(compile(SUPERVISOR_BYTES, str(SUPERVISOR_PATH), 'exec', dont_inherit=True),
     SUPERVISOR.__dict__)
IMPLEMENTATION_SHA256 = SUPERVISOR.IMPLEMENTATION_SHA256
SupervisedProcess = SUPERVISOR.SupervisedProcess
SupervisionError = SUPERVISOR.SupervisionError

# Generated directories are never source, but only the experiment root's
# target directory is generated build output: nested target directories can
# contain source, mirroring source_inputs and build_source_manifest.
ALWAYS_IGNORED = ('.git', '__pycache__')
ATTEMPT_SCHEMA = 'experiment-attempt-v1'
RECOVERY_PROCESS_WAIT = 2.0


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
            'runner_sha256': LOADED_RUNNER_SHA256,
            'supervisor_sha256': IMPLEMENTATION_SHA256}


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
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


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


def valid_attempt_name(name):
    return (isinstance(name, str) and name.startswith('attempt-')
            and Path(name).name == name)


def retained_result_valid(record, admission, key, destination):
    name = record.get('attempt', '')
    if not valid_attempt_name(name) or not reusable_result(record, admission, key):
        return False
    attempt = destination / name
    try:
        return (admitted_inputs_match(admission)
                and not attempt.is_symlink()
                and manifest(attempt / 'source') == admission['source']
                and artifacts(attempt) == record['artifacts'])
    except (KeyError, OSError, ValueError):
        return False


def read_json_receipt(path):
    if linked_source(path) or not path.is_file():
        raise ValueError('retained receipt must be a real file')
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('retained receipt must contain an object')
    return value


def retain_receipt_history(destination, receipt_path):
    """Keep an invalidated latest pointer before a retry replaces it."""
    if linked_source(receipt_path) or not receipt_path.is_file():
        raise ValueError('retained receipt must be a real file')
    payload = receipt_path.read_bytes()
    history = destination / 'receipt-history'
    history.mkdir(exist_ok=True)
    if linked_source(history) or not history.is_dir():
        raise ValueError('receipt history must be a real directory')
    target = history / ('latest-' + digest(payload) + '.json')
    if target.exists():
        if linked_source(target) or not target.is_file() or target.read_bytes() != payload:
            raise ValueError('retained receipt history collision')
        return target.name
    with target.open('xb') as stream:
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    sync_directory(history)
    return target.name


def partial_artifacts(attempt):
    """Hash only partial logs/output; incomplete data is evidence, never a result."""
    result = {}
    paths = [attempt / 'stdout.log', attempt / 'stderr.log']
    output = attempt / 'output'
    if output.exists():
        if linked_source(output) or not output.is_dir():
            raise ValueError('partial output must be a real directory')
        paths.extend(sorted(output_paths(output)))
    for path in paths:
        if not path.exists():
            continue
        if linked_source(path):
            raise ValueError('partial output links are unsupported')
        if path.is_file():
            result[path.relative_to(attempt).as_posix()] = {
                'sha256': digest(path.read_bytes()),
                'executable': bool(path.stat().st_mode & 0o111),
                'execute_bits': path.stat().st_mode & 0o111,
            }
        elif path.is_dir():
            result[path.relative_to(attempt).as_posix() + '/'] = {'directory': True}
        else:
            raise ValueError('special partial output files are unsupported')
    return result


def validate_attempt_metadata(metadata, name):
    inputs = metadata.get('inputs')
    state = metadata.get('state')
    if (metadata.get('schema') != ATTEMPT_SCHEMA or metadata.get('attempt') != name
            or not valid_attempt_name(name) or not isinstance(inputs, dict)
            or not isinstance(metadata.get('key'), str)
            or digest(json.dumps(inputs, sort_keys=True).encode()) != metadata['key']
            or state not in ('staging', 'running', 'interrupted', 'completed', 'published')
            or type(metadata.get('created_ns')) is not int):
        raise ValueError('invalid retained attempt metadata')
    if state in ('completed', 'published') and not isinstance(metadata.get('result'), dict):
        raise ValueError('completed attempt is missing its result')
    return metadata


def retained_group_active(metadata):
    group = metadata.get('process_group')
    guardian = metadata.get('guardian_pid')
    trial = metadata.get('trial_pid')
    if not all(type(value) is int and value > 0 for value in (group, guardian, trial)):
        return False
    for pid, expected in ((guardian, guardian), (trial, group)):
        try:
            if os.getpgid(pid) == expected == group:
                return True
        except ProcessLookupError:
            pass
    return False


def recover_attempts(destination, current_key):
    """Close stale attempt states and return completed candidates for recovery."""
    recovered, completed = [], []
    for attempt in sorted(destination.glob('attempt-*')):
        if attempt.is_symlink() or not attempt.is_dir():
            recovered.append({'attempt': attempt.name, 'state': 'invalid',
                              'reason': 'attempt path is not a real directory'})
            continue
        path = attempt / 'attempt.json'
        if not path.exists():
            continue  # Legacy attempt; latest.json remains its only admission path.
        try:
            metadata = validate_attempt_metadata(read_json_receipt(path), attempt.name)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            recovered.append({'attempt': attempt.name, 'state': 'invalid',
                              'reason': str(error)})
            continue
        if metadata['state'] == 'completed':
            completed.append(metadata)
            continue
        if metadata['state'] in ('interrupted', 'published'):
            continue
        deadline = time.monotonic() + RECOVERY_PROCESS_WAIT
        while retained_group_active(metadata) and time.monotonic() < deadline:
            time.sleep(.02)
        if retained_group_active(metadata):
            raise ValueError('retained attempt process group is still active')
        try:
            partial = partial_artifacts(attempt)
            partial_error = None
        except (OSError, ValueError) as error:
            partial, partial_error = {}, str(error)
        metadata = dict(metadata, state='interrupted', interrupted_ns=time.time_ns(),
                        reason='runner terminated before completed result publication',
                        partial_artifacts=partial,
                        retry_identity_matches=metadata['key'] == current_key)
        if partial_error:
            metadata['partial_artifact_error'] = partial_error
        atomic_json(path, metadata)
        recovered.append({'attempt': attempt.name, 'state': 'interrupted',
                          'retry_identity_matches': metadata['retry_identity_matches']})
    return recovered, sorted(completed, key=lambda value: value['created_ns'], reverse=True)


def mark_attempt_interrupted(attempt, metadata, reason, current_key):
    try:
        partial = partial_artifacts(attempt)
        partial_error = None
    except (OSError, ValueError) as error:
        partial, partial_error = {}, str(error)
    value = dict(metadata, state='interrupted', interrupted_ns=time.time_ns(),
                 reason=reason, partial_artifacts=partial,
                 retry_identity_matches=metadata['key'] == current_key)
    if partial_error:
        value['partial_artifact_error'] = partial_error
    atomic_json(attempt / 'attempt.json', value)


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
        recovered, completed = recover_attempts(destination, key)
        receipt_history = []
        if receipt_path.exists():
            try:
                previous = read_json_receipt(receipt_path)
            except (OSError, ValueError, json.JSONDecodeError):
                previous = None
            if previous is not None and retained_result_valid(previous, admission, key, destination):
                for metadata in completed:
                    if metadata['attempt'] == previous['attempt']:
                        atomic_json(destination / metadata['attempt'] / 'attempt.json',
                                    dict(metadata, state='published',
                                         published_ns=time.time_ns()))
                        break
                return dict(previous, reused=True, recovered_attempts=recovered)
            receipt_history.append(retain_receipt_history(destination, receipt_path))
        # A crash after the attempt receipt was synced but before latest.json
        # moved must not require re-running an already completed valid trial.
        for metadata in completed:
            previous = metadata['result']
            if retained_result_valid(previous, admission, key, destination):
                atomic_json(receipt_path, previous)
                atomic_json(destination / metadata['attempt'] / 'attempt.json',
                            dict(metadata, state='published', published_ns=time.time_ns()))
                return dict(previous, reused=True, recovered=True,
                            recovered_attempts=recovered,
                            receipt_history=receipt_history)
        attempt = destination / ('attempt-' + uuid.uuid4().hex)
        attempt.mkdir()
        sync_directory(destination)
        attempt_metadata = {
            'schema': ATTEMPT_SCHEMA, 'attempt': attempt.name, 'state': 'staging',
            'created_ns': time.time_ns(), 'key': key, 'inputs': admission,
        }
        atomic_json(attempt / 'attempt.json', attempt_metadata)
        copied, work, output = (attempt / x for x in ('source', 'work', 'output'))
        try:
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
                process = None
                try:
                    if not admitted_inputs_match(admission):
                        raise OSError('declared input changed before launch')
                    process = SupervisedProcess.start(
                        argv, executable=admission['executable'], cwd=work,
                        stdout=stdout, stderr=stderr, env=environment,
                    )
                except OSError as error:
                    reason = 'process start failed'
                    stderr.write((str(error) + '\n').encode('utf-8', errors='replace'))
                except SupervisionError as error:
                    reason = f'process supervision failed: {error}'
                else:
                    try:
                        attempt_metadata = dict(
                            attempt_metadata, state='running', guardian_pid=process.guardian.pid,
                            process_group=process.process_group, trial_pid=process.trial_pid,
                        )
                        atomic_json(attempt / 'attempt.json', attempt_metadata)
                        code = process.wait(timeout=timeout)
                        status = 'pass' if code == 0 else 'fail' if code == 1 else 'error'
                    except subprocess.TimeoutExpired:
                        reason = 'timeout'
                    except SupervisionError as error:
                        reason = f'process supervision failed: {error}'
                    finally:
                        try:
                            process.terminate()
                        except SupervisionError as error:
                            status, reason = 'error', f'process cleanup failed: {error}'
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
                      'artifacts': retained, 'reused': False,
                      'recovered_attempts': recovered, 'receipt_history': receipt_history}
            attempt_metadata = dict(attempt_metadata, state='completed',
                                    completed_ns=time.time_ns(), result=record)
            atomic_json(attempt / 'attempt.json', attempt_metadata)
            atomic_json(receipt_path, record)
            attempt_metadata = dict(attempt_metadata, state='published',
                                    published_ns=time.time_ns())
            atomic_json(attempt / 'attempt.json', attempt_metadata)
            return record
        except BaseException as error:
            try:
                mark_attempt_interrupted(
                    attempt, attempt_metadata,
                    f'runner aborted before result publication: {type(error).__name__}', key,
                )
            except (OSError, ValueError):
                pass
            raise


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
