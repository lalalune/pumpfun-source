#!/usr/bin/env python3
"""Search driver for the brute-force-grammar lane.

  python3 -B search.py singles            # every single-site alternative
  python3 -B search.py beam [--width K] [--rounds R] [--sites a,b,...]
  python3 -B search.py list FILE.json     # explicit list of choice dicts
  python3 -B search.py frontier [N]

Results: results.jsonl (one line per evaluated choice) next to this file.
"""
import json, subprocess, sys, threading, queue, time, argparse, itertools, random
from pathlib import Path
import grammar

HERE = Path(__file__).resolve().parent
SWARM = HERE.parents[1]
RES = HERE / 'results.jsonl'
VAR = HERE / 'variants'
VAR.mkdir(exist_ok=True)
LANE = 'brute-force-grammar'
lock = threading.Lock()
PRIORITY = ['owner', 'borrow', 'check', 'drop', 'else', 'empty', 'mutdrop', 'mutborrow',
            'acc_from', 'ata_key', 'ata_w', 'ata_empty', 'ata_cpi', 'ata_close', 'ata_from']


def load():
    out = {}
    if RES.exists():
        for line in RES.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                out[r['ckey']] = r
    return out


def score(r):
    if not r or r.get('status') not in ('scored', 'GOAL_SELL_RAW_EQUAL'):
        return (9, 10**9, 10**9)
    m = r
    pen = 0 if m.get('lost') == 0 else 2
    return (pen, m.get('dist', 10**9), m.get('slots', 10**9))


def run_one(choice, slot, tag):
    ck = grammar.key_of(choice) or 'pristine'
    try:
        text = grammar.render(choice)
        err = grammar.check(text)
    except ValueError as e:
        err = str(e)
    if err:
        return {'ckey': ck, 'choice': choice, 'status': 'invalid', 'err': err}
    f = VAR / (ck.replace(',', '__').replace('=', '-')[:200] + '.rs')
    f.write_text(text)
    hyp = f'grammar combo [{ck}] ({tag})'
    p = subprocess.run([sys.executable, '-B', 'harness/try_sell.py', '--lane', LANE,
                        '--approach', 'grammar-' + tag, '--hypothesis', hyp, '--sell', str(f),
                        '--slot', str(slot)], cwd=SWARM, capture_output=True, text=True)
    try:
        j = json.loads(p.stdout[p.stdout.index('{'):])
    except Exception:
        return {'ckey': ck, 'choice': choice, 'status': 'harness_error', 'err': p.stderr[-500:], 'rc': p.returncode}
    m = j.get('metrics') or {}
    r = {'ckey': ck, 'choice': choice, 'status': j.get('status'), 'key': j.get('key'),
         'dup': bool(j.get('duplicate')), 'dist': m.get('align_distance'), 'slots': m.get('slot_diffs'),
         'size': m.get('sell_size'), 'lost': m.get('lost_windows_normalized_count'),
         'borrow': m.get('borrow_branch'), 'cand_sha': j.get('candidate_sha256'),
         'errors': j.get('errors', [])[:3], 'rc': p.returncode, 'out_dir': j.get('out_dir')}
    return r


def evaluate(choices, tag, nslots=3):
    done = load()
    todo = []
    seen = set()
    for c in choices:
        c = {k: v for k, v in c.items() if v}
        ck = grammar.key_of(c) or 'pristine'
        if ck in done or ck in seen:
            continue
        seen.add(ck)
        todo.append(c)
    q = queue.Queue()
    for c in todo:
        q.put(c)
    results = []

    def worker(slot):
        while True:
            try:
                c = q.get_nowait()
            except queue.Empty:
                return
            r = run_one(c, slot, tag)
            with lock:
                with RES.open('a') as fh:
                    fh.write(json.dumps(r, sort_keys=True) + '\n')
                results.append(r)
                print(f"[{time.strftime('%H:%M:%S')}] s{slot} {r['status']:<14} d={r.get('dist')} sl={r.get('slots')} "
                      f"sz={r.get('size')} lost={r.get('lost')} br={str(r.get('borrow'))[:40]} :: {r['ckey']}", flush=True)
                if r.get('rc') == 3:
                    print('!!!!! GOAL REACHED', r, flush=True)
                    (HERE / 'GOAL.json').write_text(json.dumps(r, indent=1))
    ts = [threading.Thread(target=worker, args=(s,)) for s in range(nslots)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return results


def singles():
    cs = []
    for name in PRIORITY + [s for s in grammar.SITES if s not in PRIORITY]:
        for i in range(1, len(grammar.SITES[name])):
            cs.append({name: i})
    evaluate(cs, 'singles')


def neighbors(c, sites):
    for s in sites:
        for i in range(len(grammar.SITES[s])):
            if c.get(s, 0) != i:
                d = dict(c)
                d[s] = i
                yield {k: v for k, v in d.items() if v}


def bad_alts():
    """alts for which every evaluated combo failed (build_failed/invalid/harness_error) -> skip."""
    ok, badc = set(), set()
    for r in load().values():
        good = r['status'] in ('scored', 'GOAL_SELL_RAW_EQUAL') and r.get('lost') == 0
        for kv in r['choice'].items():
            (ok if good else badc).add(tuple(kv))
    return badc - ok


def beam(width, rounds, sites, per_round):
    bad = bad_alts()
    for rd in range(rounds):
        done = load()
        ok = [r for r in done.values() if score(r)[0] < 9]
        ok.sort(key=score)
        frontier = []
        fps = set()
        for r in ok:  # dedupe by candidate binary
            if r.get('cand_sha') in fps:
                continue
            fps.add(r.get('cand_sha'))
            frontier.append(r)
            if len(frontier) >= width:
                break
        cands = []
        for r in frontier:
            for n in neighbors(r['choice'], sites):
                if any((k, v) in bad for k, v in n.items()):
                    continue
                ck = grammar.key_of(n) or 'pristine'
                if ck not in done:
                    cands.append((score(r), random.random(), n))
        cands.sort(key=lambda t: (t[0], t[1]))
        batch = [n for _, _, n in cands[:per_round]]
        if not batch:
            print('beam: no new candidates')
            return
        print(f'beam round {rd}: frontier best {[score(r) for r in frontier[:3]]} batch {len(batch)}', flush=True)
        evaluate(batch, 'beam')
        if (HERE / 'GOAL.json').exists():
            return


def frontier(n):
    done = load()
    ok = sorted([r for r in done.values() if score(r)[0] < 9], key=score)
    for r in ok[:n]:
        print(score(r), r.get('borrow'), r.get('key', '')[:16], r['ckey'])
    from collections import Counter
    print(Counter(r['status'] for r in done.values()))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('mode')
    ap.add_argument('arg', nargs='?')
    ap.add_argument('--width', type=int, default=4)
    ap.add_argument('--rounds', type=int, default=5)
    ap.add_argument('--per-round', type=int, default=24)
    ap.add_argument('--sites', default='')
    ap.add_argument('--slots', type=int, default=3)
    a = ap.parse_args()
    if a.mode == 'singles':
        singles()
    elif a.mode == 'beam':
        sites = a.sites.split(',') if a.sites else list(grammar.SITES)
        beam(a.width, a.rounds, sites, a.per_round)
    elif a.mode == 'list':
        evaluate(json.loads(Path(a.arg).read_text()), 'list', a.slots)
    elif a.mode == 'frontier':
        frontier(int(a.arg or 20))
