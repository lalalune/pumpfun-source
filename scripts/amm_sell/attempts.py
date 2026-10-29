#!/usr/bin/env python3
"""Query and annotate the swarm attempt log (ATTEMPTS.jsonl).

  attempts.py summary                       counts per lane/approach, best results
  attempts.py best [N]                      N best non-losing attempts (default 10)
  attempts.py grep TEXT                     attempts/notes whose hypothesis/text contains TEXT
  attempts.py approaches                    distinct approach tags with counts and best distance
  attempts.py seen FILE                     was this exact sell.rs already built? (by sha256)
  attempts.py note --lane L --approach A --kind finding|dead-end|idea|target --text "..." [--data JSON]

Notes record analysis results that are not builds (dead ends, IR targets, mechanisms),
so later waves do not repeat them.
"""
from pathlib import Path
import argparse
import collections
import datetime
import fcntl
import hashlib
import json
import os
import sys
import uuid

SWARM = Path(os.environ.get('AMM_SELL_SWARM', Path(__file__).resolve().parent.parent)).resolve()
LOG = SWARM / 'ATTEMPTS.jsonl'
LOCK = SWARM / '.attempts.lock'


def entries():
    if not LOG.exists():
        return []
    return [json.loads(line) for line in LOG.read_text().splitlines() if line.strip()]


def short(e):
    m = e.get('metrics') or {}
    if e.get('schema') == 'amm-sell-note-v1':
        return f"[note/{e['kind']}] {e['lane']}/{e['approach']}: {e['text'][:300]}"
    return (f"{e['lane']}/{e['approach']} {e.get('status')} dist={m.get('align_distance')} slots={m.get('slot_diffs')} "
            f"lost={m.get('lost_windows_count')} size={m.get('sell_size')} :: {e['hypothesis'][:200]}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('summary')
    b = sub.add_parser('best'); b.add_argument('n', nargs='?', type=int, default=10)
    g = sub.add_parser('grep'); g.add_argument('text')
    sub.add_parser('approaches')
    s = sub.add_parser('seen'); s.add_argument('file')
    n = sub.add_parser('note')
    n.add_argument('--lane', required=True); n.add_argument('--approach', required=True)
    n.add_argument('--kind', required=True, choices=['finding', 'dead-end', 'idea', 'target', 'prior'])
    n.add_argument('--text', required=True); n.add_argument('--data')
    a = p.parse_args()
    es = entries()
    builds = [e for e in es if e.get('schema') == 'amm-sell-attempt-v1']
    if a.cmd == 'summary':
        print(f'{len(builds)} builds, {len(es) - len(builds)} notes')
        c = collections.Counter((e['lane'], e['approach']) for e in builds)
        for (lane, approach), k in sorted(c.items()):
            print(f'  {lane:28} {approach:40} {k}')
        a.cmd, a.n = 'best', 5
    if a.cmd == 'best':
        ok = [e for e in builds if (e.get('metrics') or {}).get('lost_windows_count') == 0]
        ok.sort(key=lambda e: (not e['metrics']['sell_raw_equal'], e['metrics']['align_distance'], e['metrics']['slot_diffs']))
        for e in ok[:a.n]:
            print(short(e))
    elif a.cmd == 'grep':
        t = a.text.lower()
        for e in es:
            if t in json.dumps(e).lower():
                print(short(e))
    elif a.cmd == 'approaches':
        d = collections.defaultdict(list)
        for e in builds:
            d[e['approach']].append(e)
        for k, v in sorted(d.items()):
            dist = [x['metrics']['align_distance'] for x in v if x.get('metrics')]
            print(f'{k:44} n={len(v):4} best_dist={min(dist) if dist else None}')
    elif a.cmd == 'seen':
        h = hashlib.sha256(Path(a.file).read_bytes()).hexdigest()
        hits = [e for e in builds if e['inputs']['sell'] == h]
        print(json.dumps([{'lane': e['lane'], 'approach': e['approach'], 'patch': e['inputs']['patch'],
                           'flags': e['inputs']['flags'], 'metrics': e.get('metrics'), 'status': e.get('status')}
                          for e in hits], indent=1) if hits else 'unseen')
    elif a.cmd == 'note':
        entry = {'schema': 'amm-sell-note-v1', 'attempt_id': uuid.uuid4().hex,
                 'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'lane': a.lane, 'approach': a.approach, 'kind': a.kind, 'text': a.text,
                 'data': json.loads(a.data) if a.data else None}
        with LOCK.open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            with LOG.open('a') as log:
                log.write(json.dumps(entry, sort_keys=True) + '\n')
            fcntl.flock(lock, fcntl.LOCK_UN)
        print('logged', entry['attempt_id'])


if __name__ == '__main__':
    main()
