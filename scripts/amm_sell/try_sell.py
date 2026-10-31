#!/usr/bin/env python3
"""Build, score and log ONE sell attempt, deduplicated across the whole swarm.

  try_sell.py --lane LANE --approach TAG --hypothesis "why this might match" \
      (--sell FILE | --patch FILE | --baseline) [--slot N] [--extra-root-flags "..."] \
      [--link-script FILE] [--disasm] [--force]

* --sell FILE   full replacement for programs/pump-amm/src/instructions/swap/sell.rs
* --patch FILE  unified diff (-p1) against the pristine workspace root (may touch any file)
* --slot N      independent build directory inside the lane (parallel builds in one lane)
* Cache inputs bind the complete selected baseline, harness, SDK and listing request,
  as well as sell bytes + patch bytes + flags + link script. Only a repeat with
  intact retained outputs returns "duplicate": true and is NOT re-logged.
* Every executed attempt is appended to ATTEMPTS.jsonl (flock) and its sell.rs is kept in
  sources/<sha256>.rs. BEST-v<SCORE_VERSION>.json tracks the best non-losing attempt.

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
import tempfile
import uuid

HERE = Path(__file__).resolve().parent
SWARM = Path(os.environ.get('AMM_SELL_SWARM', HERE.parent)).resolve()
sys.path.insert(0, str(HERE))
import native_build  # noqa: E402
import sell_score  # noqa: E402
import cache_inputs  # noqa: E402
from ledger_io import append_entry  # noqa: E402

LOG = SWARM / 'ATTEMPTS.jsonl'
LOCK = SWARM / '.attempts.lock'
CACHE = SWARM / 'cache'
SOURCES = SWARM / 'sources'
BEST = SWARM / f'BEST-v{sell_score.SCORE_VERSION}.json'
PRISTINE_SELL = SWARM / 'baselines/pristine-ws' / native_build.SELL_REL


def sha(data):
    return hashlib.sha256(data).hexdigest()


def input_snapshot(baseline, *, sell, patch, flags, link_script, want_disasm):
    blobs = {'sell': Path(sell).read_bytes() if sell else (baseline / native_build.SELL_REL).read_bytes(),
             'patch': Path(patch).read_bytes() if patch is not None else None,
             'link': Path(link_script).read_bytes() if link_script is not None else None}
    key_doc = {'score_version': sell_score.SCORE_VERSION,
               **{name: sha(data) if data is not None else None for name, data in blobs.items()},
               'flags': flags.strip(),
               'context': cache_inputs.context(SWARM, HERE, baseline, Path(sell_score.elf_reader.__file__), want_disasm)}
    return key_doc, blobs


def retain_input(data, suffix):
    """Publish complete admitted bytes before another attempt can read them."""
    path = SOURCES / (sha(data) + suffix)
    descriptor, temporary = tempfile.mkstemp(prefix='.input-', dir=SOURCES)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path


def locked_append(entry):
    with LOCK.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        append_entry(LOG, entry)
        # Historical distances remain loggable, but cannot update the current scale's best.
        current = (entry.get('metrics') or {}).get('score_version') == sell_score.SCORE_VERSION
        r = sell_score.rank(entry) if current else None
        if r is not None:
            best = json.loads(BEST.read_text()) if BEST.exists() else None
            if best is None or r < tuple(best['rank']):
                # A torn BEST would stop every later attempt at the read above.
                temporary = BEST.with_name('.' + BEST.name + '.tmp')
                try:
                    temporary.write_text(json.dumps({'rank': list(r), 'entry': entry}, indent=1, sort_keys=True) + '\n')
                    os.replace(temporary, BEST)
                finally:
                    temporary.unlink(missing_ok=True)
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

    lane_build = SWARM / 'lanes' / a.lane / ('build' + a.slot)
    baseline = lane_build / 'baseline-ws'
    if not baseline.exists():
        baseline = native_build.PRISTINE
    key_doc, blobs = input_snapshot(baseline, sell=a.sell, patch=a.patch,
                                    flags=a.extra_root_flags, link_script=a.link_script, want_disasm=a.disasm)
    key = sha(json.dumps(key_doc, sort_keys=True).encode())
    CACHE.mkdir(exist_ok=True)
    SOURCES.mkdir(exist_ok=True)
    cached = CACHE / (key + '.json')
    if cached.exists() and not a.force:
        try:
            result = json.loads(cached.read_text())
        except (OSError, ValueError):
            result = {}
        if cache_inputs.admitted(result, key, key_doc, SWARM):
            result['duplicate'] = True
            print(json.dumps(result, indent=1))
            if result.get('status') == 'build_failed':
                return 2
            return 3 if (result.get('metrics') or {}).get('sell_raw_equal') else 0
    retained = {name: retain_input(data, {'sell': '.rs', 'patch': '.patch', 'link': '.ld'}[name])
                for name, data in blobs.items() if data is not None}
    build_id = key[:16]
    record = native_build.build(lane_build, build_id, sell=retained['sell'] if a.sell else None,
                                patch=retained.get('patch'), extra_root_flags=a.extra_root_flags,
                                link_script=str(retained['link']) if 'link' in retained else None)
    out = Path(record.get('output_dir') or lane_build / 'out' / build_id)
    entry = {'schema': 'amm-sell-attempt-v1', 'attempt_id': uuid.uuid4().hex,
             'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'lane': a.lane, 'approach': a.approach, 'hypothesis': a.hypothesis, 'key': key,
             'inputs': key_doc, 'out_dir': str(out), 'build_seconds': record.get('seconds')}
    if record['returncode'] != 0:
        log = (out / 'build.log').read_text(errors='replace').splitlines()
        errors = (record['stack_warnings'] + [line for line in log if line.startswith('error')])[:12]
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
    if cache_inputs.context(SWARM, HERE, baseline, Path(sell_score.elf_reader.__file__), a.disasm) != key_doc['context']:
        raise RuntimeError('cache inputs changed during the attempt; outputs retained without publishing a cache hit')
    entry['output_sha256'] = cache_inputs.outputs(entry, SWARM)
    cache_inputs.publish(cached, entry)
    locked_append(entry)
    print(json.dumps(entry, indent=1, sort_keys=True))
    return code


if __name__ == '__main__':
    sys.exit(main())
