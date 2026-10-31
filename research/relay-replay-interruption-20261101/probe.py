"""Exercise the real replay supervisor with owned ordinary host processes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

RELATIVE = 'reconstruction/donation-relay/native-linux-v148-20261030/replay.py'
CHILD = '''import os, signal, subprocess, sys, time
from pathlib import Path
root, role, ignore_term = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
if ignore_term == 'yes' or (ignore_term == 'grandchild' and role == 'grandchild'):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
(root / (role + '.pid')).write_text(str(os.getpid()))
if role == 'leader':
    subprocess.Popen([sys.executable, '-B', __file__, str(root), 'grandchild', sys.argv[3]])
    deadline = time.monotonic() + 5
    while not (root / 'grandchild.pid').exists():
        if time.monotonic() > deadline:
            raise RuntimeError('grandchild readiness deadline')
        time.sleep(.01)
    (root / 'ready').touch()
while not (root / 'supervisor-returned').exists():
    time.sleep(.01)
(root / (role + '-marker')).write_text('ran after supervisor returned')
time.sleep(30)
'''
SUPERVISOR = '''import sys
from pathlib import Path
import replay
root, mode, ignore_term = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
if mode == 'record-error':
    (root / 'proof-process.json').write_text('preserve existing process record')
replay.monitored([sys.executable, '-B', str(root / 'child.py'), str(root), 'leader', ignore_term],
                 root, 'proof', 20, 0)
'''


def wait_ready(root, proc):
    deadline = time.monotonic() + 5
    while not (root / 'ready').exists():
        if proc.poll() is not None:
            raise RuntimeError('supervisor exited before child readiness')
        if time.monotonic() > deadline:
            raise RuntimeError('child readiness deadline exceeded')
        time.sleep(.01)


def case(source, mode, ignore_term=False):
    with tempfile.TemporaryDirectory(prefix='relay-monitor-proof-') as tmp:
        root = Path(tmp)
        (root / 'replay.py').write_bytes(source)
        (root / 'child.py').write_text(CHILD, encoding='utf-8')
        (root / 'supervisor.py').write_text(SUPERVISOR, encoding='utf-8')
        with (root / 'supervisor.log').open('wb') as log:
            proc = subprocess.Popen(
                [sys.executable, '-B', str(root / 'supervisor.py'), str(root), mode,
                 'yes' if ignore_term is True else ignore_term or 'no'],
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                if mode == 'interrupt':
                    wait_ready(root, proc)
                started = time.monotonic()
                if mode == 'interrupt':
                    proc.send_signal(signal.SIGINT)
                returncode = proc.wait(timeout=8)
                elapsed = time.monotonic() - started
                # This release is after the supervisor returns, including its
                # grace period. Surviving processes now make observable writes.
                (root / 'supervisor-returned').touch()
                time.sleep(.8)
                error = (root / 'supervisor.log').read_text()
                return {
                    'scenario': mode + ('-ignoring-term' if ignore_term is True else
                                        '-descendant-ignoring-term' if ignore_term else ''),
                    'supervisor_returncode': returncode,
                    'stop_seconds': round(elapsed, 3),
                    'leader_ran_after_return': (root / 'leader-marker').exists(),
                    'grandchild_ran_after_return': (root / 'grandchild-marker').exists(),
                    'original_exception_retained': (
                        'KeyboardInterrupt' if mode == 'interrupt' else 'FileExistsError') in error,
                    'process_record_retained': (root / 'proof-process.json').exists(),
                    'existing_record_preserved': mode != 'record-error' or
                        (root / 'proof-process.json').read_text() == 'preserve existing process record',
                    'log_retained': (root / 'proof.log').exists(),
                }
            finally:
                # The base is deliberately defective. Clean only fixture-owned
                # groups after observation, including on an assertion/watchdog.
                leader = root / 'leader.pid'
                if leader.exists():
                    try:
                        os.killpg(int(leader.read_text()), signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                elif (root / 'proof-process.json').exists() and mode != 'record-error':
                    try:
                        os.killpg(json.loads((root / 'proof-process.json').read_text())['pid'], signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                if proc.poll() is None:
                    proc.kill()
                proc.wait(timeout=5)


def run(repo, revision=None):
    source = (subprocess.check_output(['git', 'show', f'{revision}:{RELATIVE}'], cwd=repo)
              if revision else (repo / RELATIVE).read_bytes())
    return {
        'source_sha256': hashlib.sha256(source).hexdigest(),
        'revision': revision or 'working-tree',
        'scenarios': [case(source, 'interrupt'), case(source, 'interrupt', True),
                      case(source, 'interrupt', 'grandchild'), case(source, 'record-error')],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path)
    parser.add_argument('--revision')
    args = parser.parse_args()
    print(json.dumps(run(args.repo.resolve(), args.revision), indent=2))
