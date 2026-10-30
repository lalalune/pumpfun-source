#!/usr/bin/env python3
"""Build, score and log ONE sell attempt, deduplicated across the whole swarm.

  try_sell.py --lane LANE --approach TAG --hypothesis "why this might match" \
      (--sell FILE | --patch FILE | --baseline) [--slot N] [--extra-root-flags "..."] \
      [--link-script FILE] [--disasm] [--force]

* --sell FILE   full replacement for programs/pump-amm/src/instructions/swap/sell.rs
* --patch FILE  unified diff (-p1) against the pristine workspace root (may touch any file)
* --slot N      independent build directory inside the lane (parallel builds in one lane)
* Identical inputs (sell bytes + patch bytes + flags + link script) are built once per swarm:
  a repeat returns the cached result with "duplicate": true and is NOT re-logged.
* Every executed attempt is appended to ATTEMPTS.jsonl (flock) and its sell.rs is kept in
  sources/<sha256>.rs. BEST.json tracks the best non-losing attempt.

Exit status: 0 = built and scored, 2 = build failed, 3 = SELL RAW-EQUAL (goal reached).
"""
from pathlib import Path
import argparse
import datetime
import fcntl
import hashlib
import json
import os
import sys
import uuid

HERE = Path(__file__).resolve().parent
SWARM = Path(os.environ.get('AMM_SELL_SWARM', HERE.parent)).resolve()
sys.path.insert(0, str(HERE))
import native_build  # noqa: E402
import sell_score  # noqa: E402

LOG = SWARM / 'ATTEMPTS.jsonl'
LOCK = SWARM / '.attempts.lock'
CACHE = SWARM / 'cache'
SOURCES = SWARM / 'sources'
BEST = SWARM / 'BEST.json'
PRISTINE_SELL = SWARM / 'baselines/pristine-ws' / native_build.SELL_REL


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rank(entry):
    """Lower is better. None = regresses some other function (never 'best')."""
    m = entry.get('metrics') or {}
    if not m or m.get('lost_windows_normalized_count') != 0:
        return None
    return (0 if m.get('sell_raw_equal') else 1, 0 if m.get('sell_size') == 9024 else 1,
            m.get('align_distance', 10**9), m.get('slot_diffs', 10**9))


def locked_append(entry):
    with LOCK.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with LOG.open('a') as log:
            log.write(json.dumps(entry, sort_keys=True) + '\n')
        r = rank(entry)
        if r is not None:
            best = json.loads(BEST.read_text()) if BEST.exists() else None
            if best is None or r < tuple(best['rank']):
                BEST.write_text(json.dumps({'rank': list(r), 'entry': entry}, indent=1, sort_keys=True) + '\n')
        fcntl.flock(lock, fcntl.LOCK_UN)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--lane', required=True)
    p.add_argument('--approach', required=True, help='short kebab tag of the approach family')
    p.add_argument('--hypothesis', required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--sell')
    g.add_argument('--patch')
    g.add_argument('--baseline', action='store_true')
    p.add_argument('--slot', default='0')
    p.add_argument('--extra-root-flags', default='')
    p.add_argument('--link-script')
    p.add_argument('--disasm', action='store_true')
    p.add_argument('--force', action='store_true', help='rebuild even if identical inputs were already tried')
    a = p.parse_args()

    sell_bytes = Path(a.sell).read_bytes() if a.sell else PRISTINE_SELL.read_bytes()
    patch_bytes = Path(a.patch).read_bytes() if a.patch else b''
    link_bytes = Path(a.link_script).read_bytes() if a.link_script else b''
    key_doc = {'score_version': sell_score.SCORE_VERSION,
               'sell': sha(sell_bytes), 'patch': sha(patch_bytes) if patch_bytes else None,
               'flags': a.extra_root_flags.strip(), 'link': sha(link_bytes) if link_bytes else None}
    key = sha(json.dumps(key_doc, sort_keys=True).encode())
    CACHE.mkdir(exist_ok=True)
    SOURCES.mkdir(exist_ok=True)
    cached = CACHE / (key + '.json')
    if cached.exists() and not a.force:
        result = json.loads(cached.read_text())
        result['duplicate'] = True
        print(json.dumps(result, indent=1))
        return 3 if (result.get('metrics') or {}).get('sell_raw_equal') else 0
    (SOURCES / (key_doc['sell'] + '.rs')).write_bytes(sell_bytes)
    if patch_bytes:
        (SOURCES / (key_doc['patch'] + '.patch')).write_bytes(patch_bytes)
    lane_build = SWARM / 'lanes' / a.lane / ('build' + a.slot)
    build_id = key[:16]
    record = native_build.build(lane_build, build_id, sell=a.sell, patch=a.patch,
                                extra_root_flags=a.extra_root_flags, link_script=a.link_script)
    out = Path(record.get('output_dir') or lane_build / 'out' / build_id)
    entry = {'schema': 'amm-sell-attempt-v1', 'attempt_id': uuid.uuid4().hex,
             'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'lane': a.lane, 'approach': a.approach, 'hypothesis': a.hypothesis, 'key': key,
             'inputs': key_doc, 'out_dir': str(out), 'build_seconds': record.get('seconds')}
    if record['returncode'] != 0:
        log = (out / 'build.log').read_text(errors='replace').splitlines()
        errors = [line for line in log if line.startswith('error')][:12]
        entry.update({'status': 'build_failed', 'errors': errors})
        code = 2
    else:
        s = sell_score.score(out, want_disasm=a.disasm)
        metrics = {k: s[k] for k in ('score_version', 'sell_raw_equal', 'whole_elf_equal',
                                     'allocation_image_equal', 'unstripped_elf_equal',
                                     'original_bytes', 'candidate_bytes', 'unstripped_bytes',
                                     'allocation_padding_bytes', 'windows_raw_equal', 'sell_start',
                                     'sell_size', 'slot_diffs', 'align_distance', 'ja_count', 'cond_count')}
        metrics['lost_windows_count'] = len(s['lost_windows'])
        metrics['lost_windows'] = s['lost_windows'][:20]
        lost_norm = s['lost_windows_normalized']
        metrics['lost_windows_normalized_count'] = None if lost_norm is None else len(lost_norm)
        metrics['lost_windows_normalized'] = None if lost_norm is None else lost_norm[:20]
        metrics['candidate_windows'] = s['candidate_windows']
        metrics['borrow_branch'] = s['borrow_branch']['candidate']
        entry.update({'status': 'GOAL_SELL_RAW_EQUAL' if s['sell_raw_equal'] else 'scored',
                      'metrics': metrics, 'candidate_sha256': s['candidate_sha256'],
                      'unstripped_sha256': s['unstripped_sha256']})
        if a.disasm:
            entry['disasm'] = s.get('disasm')
        code = 3 if s['sell_raw_equal'] else 0
    cached.write_text(json.dumps(entry, indent=1, sort_keys=True) + '\n')
    locked_append(entry)
    print(json.dumps(entry, indent=1, sort_keys=True))
    return code


if __name__ == '__main__':
    sys.exit(main())
