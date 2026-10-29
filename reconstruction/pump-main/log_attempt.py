#!/usr/bin/env python3
"""Concurrency-safe, append-only attempt ledger for the main-Pump matching swarm.

The live ledger is shared by every worktree at $PUMP_SWARM_LEDGER (default
~/.cache/pumpfun-reconstruction/pump-main/ATTEMPTS.jsonl). It is seeded from the
tracked reconstruction/pump-main/ATTEMPTS.jsonl on first use, and `sync` copies it
back into a checkout so it can be committed.

  log_attempt.py check   --dedupe-key KEY
  log_attempt.py search  [--target 0x...] [--lane L] [--status S] [--text WORDS] [--limit N]
  log_attempt.py summary [--target 0x...]
  log_attempt.py record  --lane L --approach A --target 0x... --dedupe-key KEY \\
                         --hypothesis TEXT --status STATUS [--data JSON] [--pr URL]
  log_attempt.py sync    [--to PATH]

Dedupe keys must name the target, the source base and the mechanism, e.g.
0x14f4e0-main-d2cb88d-guard-merge-loop-v1. A duplicate key is rejected; do not rename an
already-tried mechanism to get past the check.
"""
import argparse
import collections
import datetime as dt
import fcntl
import hashlib
import json
import os
import shutil
import stat
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRACKED = HERE / 'ATTEMPTS.jsonl'
LEDGER = Path(os.environ.get('PUMP_SWARM_LEDGER', str(Path.home() / '.cache/pumpfun-reconstruction/pump-main/ATTEMPTS.jsonl')))
LOCK = LEDGER.with_name('.attempts.lock')
STATUSES = ['analyzed', 'built', 'compile-failed', 'rejected', 'partial', 'normalized-match', 'raw-match']


def atomic_copy(source, destination):
    """Publish complete ledger bytes without truncating the previous snapshot."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        mode = stat.S_IMODE(destination.stat().st_mode)
    except FileNotFoundError:
        mode = None
    temporary = destination.parent / f'.attempts-{uuid.uuid4().hex}.tmp'
    # Exclusive creation applies the umask without reading/changing global state.
    fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o666)
    try:
        if mode is None:
            mode = stat.S_IMODE(os.fstat(fd).st_mode)
        # Keep incomplete bytes private and writable even with a restrictive mask.
        os.fchmod(fd, 0o600)
        shutil.copyfile(source, temporary)
        os.fchmod(fd, mode)
        os.fsync(fd)
        os.replace(temporary, destination)
    finally:
        os.close(fd)
        temporary.unlink(missing_ok=True)


def read_rows():
    if not LEDGER.exists():
        return []
    rows = []
    for number, line in enumerate(LEDGER.read_text().splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f'corrupt ledger line {number}: {exc}')
    return rows


def locked(fn):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LOCK.touch(exist_ok=True)
    with LOCK.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not LEDGER.exists() and TRACKED.exists():
            atomic_copy(TRACKED, LEDGER)
        return fn(read_rows())


def matches(row, args):
    if getattr(args, 'target', None) and row.get('target') != args.target:
        return False
    if getattr(args, 'lane', None) and row.get('lane') != args.lane:
        return False
    if getattr(args, 'status', None) and row.get('status') != args.status:
        return False
    if getattr(args, 'text', None):
        blob = json.dumps(row, ensure_ascii=False).lower()
        # Preserve serialized-metadata queries and also match literal text
        # inside JSON strings (quotes and backslashes are escaped there).
        return all(word.lower() in blob or
                   json.dumps(word.lower(), ensure_ascii=False)[1:-1] in blob
                   for word in args.text.split())
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    check = sub.add_parser('check')
    check.add_argument('--dedupe-key', required=True)
    search = sub.add_parser('search')
    summary = sub.add_parser('summary')
    for p in (search, summary):
        p.add_argument('--target')
    search.add_argument('--lane')
    search.add_argument('--status', choices=STATUSES)
    search.add_argument('--text', help='space-separated words that must all appear in the row')
    search.add_argument('--limit', type=int, default=40)
    record = sub.add_parser('record')
    record.add_argument('--lane', required=True)
    record.add_argument('--approach', required=True)
    record.add_argument('--target', required=True)
    record.add_argument('--dedupe-key', required=True)
    record.add_argument('--hypothesis', required=True)
    record.add_argument('--status', required=True, choices=STATUSES)
    record.add_argument('--data', default='{}', help='JSON object with evidence paths, hashes, metrics and notes')
    record.add_argument('--pr', help='pull request URL carrying this attempt, if any')
    sync = sub.add_parser('sync')
    sync.add_argument('--to', type=Path, default=TRACKED)
    args = parser.parse_args()

    if args.command == 'check':
        def run(rows):
            dupes = [r for r in rows if r.get('dedupe_key') == args.dedupe_key]
            print(json.dumps({'dedupe_key': args.dedupe_key, 'duplicate': bool(dupes), 'attempt_ids': [r.get('attempt_id') for r in dupes]}))
        return locked(run)

    if args.command == 'search':
        def run(rows):
            hits = [r for r in rows if matches(r, args)]
            # hits[-0:] is the whole list, so an explicit zero must be handled.
            shown = hits[-args.limit:] if args.limit else []
            for r in shown:
                data = r.get('data') or {}
                note = data.get('result') or data.get('notes') or data.get('outcome') or ''
                print(json.dumps({k: r.get(k) for k in ['timestamp_utc', 'lane', 'target', 'status', 'dedupe_key', 'hypothesis']} | {'note': str(note)[:300]}))
            print(f'# {len(hits)} matching rows ({len(shown)} shown, newest last)')
        return locked(run)

    if args.command == 'summary':
        def run(rows):
            by = collections.defaultdict(list)
            for r in rows:
                if not args.target or r.get('target') == args.target:
                    by[r.get('target')].append(r)
            for target, rs in sorted(by.items(), key=lambda kv: -len(kv[1])):
                print(json.dumps({'target': target, 'attempts': len(rs), 'statuses': dict(collections.Counter(r['status'] for r in rs)),
                                  'lanes': sorted({r['lane'] for r in rs}), 'approaches': sorted({r['approach'] for r in rs})}))
        return locked(run)

    if args.command == 'sync':
        def run(rows):
            args.to.parent.mkdir(parents=True, exist_ok=True)
            atomic_copy(LEDGER, args.to)
            print(json.dumps({'synced': str(args.to), 'attempts': len(rows), 'sha256': hashlib.sha256(args.to.read_bytes()).hexdigest()}))
        return locked(run)

    data = json.loads(args.data)
    if not isinstance(data, dict):
        raise SystemExit('--data must be a JSON object')

    def run(rows):
        if any(r.get('dedupe_key') == args.dedupe_key for r in rows):
            raise SystemExit(f'duplicate dedupe key: {args.dedupe_key}; attempt already logged')
        row = {
            'schema': 'main-pump-attempt-v1',
            'attempt_id': uuid.uuid4().hex,
            'timestamp_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
            'lane': args.lane,
            'approach': args.approach,
            'target': args.target,
            'dedupe_key': args.dedupe_key,
            'hypothesis': args.hypothesis,
            'status': args.status,
            'data': data | ({'pr': args.pr} if args.pr else {}),
        }
        # read_rows accepts a final JSON record without a newline. Keep that
        # record separate when appending, under the existing exclusive lock.
        separator = ''
        if LEDGER.exists() and LEDGER.stat().st_size:
            with LEDGER.open('rb') as current:
                current.seek(-1, os.SEEK_END)
                if current.read(1) != b'\n':
                    separator = '\n'
        with LEDGER.open('a') as output:
            output.write(separator)
            output.write(json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n')
            output.flush()
            os.fsync(output.fileno())
        print(json.dumps({'recorded': True, 'attempt_id': row['attempt_id'], 'attempts': len(rows) + 1}))
    return locked(run)


if __name__ == '__main__':
    main()
