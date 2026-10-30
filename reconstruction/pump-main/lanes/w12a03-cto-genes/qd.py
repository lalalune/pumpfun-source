#!/usr/bin/env python3
"""Queue daemon for admin_cto gene/composite trials (lane w12a03-cto-genes).

  qd.py            run trials from $OUT/queue.txt with 2 workers until $OUT/STOP exists

queue.txt holds one trial per line, `name=gene1+gene2+...`, highest priority first; it is re-read
whenever a worker is free, so new composites can be inserted at the top while the daemon runs.
A trial already in results.jsonl (or in the ledger under its dedupe key) is skipped. A trial whose
measure.sh finished without a recorded row (daemon restart) is adopted from its $OUT/t/<name> files.
"""
import json, os, subprocess, sys, threading, shutil, time, difflib, importlib.util
from pathlib import Path

LANE = 'w12a03-cto-genes'
SWARM = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm')
WT = SWARM / 'worktrees' / LANE
OUT = Path.home() / '.cache/pumpfun-reconstruction/lanes' / LANE
TOOLS = SWARM / 'w11/tools'
LEDGER = WT / 'reconstruction/pump-main/log_attempt.py'
REL = 'src/creator/admin_cto.rs'
MAIN7 = os.environ.get('GENE_MAIN7', '20a1ae9')
BASE = {'ratio': 0.43919, 'bytes': 27400, 'slots': 3352}
BASESCORE = Path.home() / '.cache/pumpfun-reconstruction/w11/current-baseline/score.json'
NPAR = int(os.environ.get('GENE_PAR', '2'))
RES = OUT / 'results.jsonl'
QUEUE = OUT / 'queue.txt'
BASEFILE = WT / 'programs/pump' / REL

spec = importlib.util.spec_from_file_location('genes', str(Path(__file__).resolve().parent / 'genes.py'))
lock = threading.Lock()
running = set()


def load_genes():
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def done():
    d = {}
    if RES.exists():
        for l in RES.read_text().splitlines():
            if l.strip():
                r = json.loads(l); d[r['name']] = r
    return d


def ledger_dup(key):
    r = subprocess.run(['python3', str(LEDGER), 'check', '--dedupe-key', key], capture_output=True, text=True)
    try:
        return bool(json.loads(r.stdout.strip().splitlines()[-1]).get('duplicate'))
    except Exception:
        return False


def summarize(out):
    """Rebuild measure.sh's JSON line from an out dir."""
    s = json.load(open(out / 'score.json'))
    b = json.load(open(BASESCORE))['windows']
    w = s['windows']
    hx = lambda k: hex(int(k))
    def tm(p):
        try:
            d = json.loads(open(p).read() or '{}')
        except Exception:
            return {}
        return {k: d.get(k) for k in ('ratio', 'slots_diff', 'cand_bytes', 'window_bytes', 'normalized_equal', 'raw_equal', 'calls_candidate')}
    return {'ok': True, 'sha': s['summary'].get('candidate_sha256', '')[:16],
            'normalized': sum(1 for x in w.values() if x['normalized']), 'raw': sum(1 for x in w.values() if x['raw']),
            'losses': [hx(k) for k in b if b[k]['normalized'] and not w.get(k, {}).get('normalized')],
            'raw_losses': [hx(k) for k in b if b[k]['raw'] and not w.get(k, {}).get('raw')],
            'gains': [hx(k) for k in w if w[k]['normalized'] and not b.get(k, {}).get('normalized')],
            'raw_gains': [hx(k) for k in w if w[k]['raw'] and not b.get(k, {}).get('raw')],
            'swap_hop': tm(out / 'hop.json'), 'admin_cto': tm(out / 'cto.json'), 'out': str(out)}


def run_trial(name, glist, w):
    genes = load_genes()
    key = f'0x22a10-w12-{MAIN7}-gene-{name}-v1'
    base = BASEFILE.read_text()
    try:
        text = genes.apply(base, glist)
    except Exception as e:
        row = {'name': name, 'genes': glist, 'status': 'apply-failed', 'error': str(e)}
        with lock:
            RES.open('a').write(json.dumps(row) + '\n')
        print(json.dumps({'name': name, 'status': 'apply-failed', 'error': str(e)[:200]}), flush=True)
        return
    tout = OUT / 't' / name
    t0 = time.time()
    adopted = (tout / 'cto.json').exists() and (tout / 'score.json').exists() and (tout / 'cto.json').stat().st_size > 0
    if adopted:
        m = summarize(tout)
    else:
        var = OUT / 'var' / name
        if var.exists():
            shutil.rmtree(var)
        var.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['rsync', '-a', '--exclude', 'target', f'{WT}/programs/pump/', f'{var}/'], check=True)
        (var / REL).write_text(text)
        r = subprocess.run([str(TOOLS / 'measure.sh'), str(var), str(OUT / f'work{w}'), str(tout)], capture_output=True, text=True)
        line = (r.stdout.strip().splitlines() or ['{}'])[-1]
        try:
            m = json.loads(line)
        except Exception:
            m = {'ok': False, 'error': r.stdout[-800:] + r.stderr[-800:]}
        shutil.rmtree(var, ignore_errors=True)
    secs = int(time.time() - t0)
    diff = ''.join(difflib.unified_diff(base.splitlines(True), text.splitlines(True), 'main/admin_cto.rs', f'{name}/admin_cto.rs', n=0))
    row = {'name': name, 'genes': glist, 'secs': secs, 'key': key, 'adopted': adopted}
    if not m.get('ok'):
        err = str(m.get('error', ''))
        try:
            err = (tout / 'build.err').read_text()[-1500:] + err
        except Exception:
            pass
        row.update(status='compile-failed', error=err[-900:])
    else:
        c = m.get('admin_cto') or {}
        row.update(ratio=c.get('ratio'), bytes=c.get('cand_bytes'), slots=c.get('slots_diff'), calls=c.get('calls_candidate'),
                   normalized=m['normalized'], raw=m['raw'], losses=m['losses'], raw_losses_n=len(m['raw_losses']),
                   raw_losses=m['raw_losses'][:5], gains=m['gains'], raw_gains=m['raw_gains'][:5], sha=m['sha'],
                   hop=m.get('swap_hop'), out=m['out'])
        row['d_bytes'] = (row['bytes'] or 0) - BASE['bytes']
        row['d_ratio'] = round((row['ratio'] or 0) - BASE['ratio'], 5)
        try:
            fr = json.loads(subprocess.run(['python3', str(Path(__file__).resolve().parent / 'frame.py'), str(Path(m['out']) / 'unstripped.so')],
                                           capture_output=True, text=True, timeout=120).stdout.strip().splitlines()[-1])
            row['frame_first'] = fr.get('first_store_dec'); row['frame_common'] = fr.get('common_with_orig'); row['frame_n'] = fr.get('n')
        except Exception:
            pass
        zero = not m['losses'] and not m['raw_losses']
        better = zero and row['bytes'] == 27400 and (row['ratio'] or 0) > BASE['ratio']
        row['status'] = 'partial' if better else 'built'
        keep = better or (row['bytes'] == 27400 and zero)
        if not keep:
            for so in ('unstripped.so', 'candidate.so'):
                p = Path(m['out']) / so
                if p.exists():
                    p.unlink()
    row['diff'] = diff
    with lock:
        RES.open('a').write(json.dumps(row) + '\n')
    data = {'output': row.get('out', ''), 'normalized': row.get('normalized'), 'raw': row.get('raw'), 'losses': row.get('losses', []),
            'raw_losses': row.get('raw_losses', []), 'target': {'ratio': row.get('ratio'), 'slots_diff': row.get('slots'), 'cand_bytes': row.get('bytes')},
            'notes': f'gene trial {"+".join(glist) or "main"} on main {MAIN7}: d_bytes {row.get("d_bytes")} d_ratio {row.get("d_ratio")}'}
    if not ledger_dup(key):
        subprocess.run(['python3', str(LEDGER), 'record', '--lane', LANE, '--approach', 'gene-harvest', '--target', '0x22a10', '--dedupe-key', key,
                        '--hypothesis', (f'gene set {"+".join(glist) or "main"} on main {MAIN7}: ' + '; '.join(genes.SRC.get(g, '?') for g in glist))[:600],
                        '--status', row['status'], '--data', json.dumps(data)], capture_output=True, text=True)
    print(json.dumps({k: row.get(k) for k in ('name', 'status', 'bytes', 'd_bytes', 'ratio', 'd_ratio', 'slots', 'normalized', 'raw', 'raw_losses_n', 'secs', 'adopted')}), flush=True)


def next_trial():
    have = done()
    if not QUEUE.exists():
        return None
    for l in QUEUE.read_text().splitlines():
        l = l.strip()
        if not l or l.startswith('#'):
            continue
        name, _, gs = l.partition('=')
        if name in have or name in running:
            continue
        glist = [g for g in gs.split('+') if g]
        key = f'0x22a10-w12-{MAIN7}-gene-{name}-v1'
        if ledger_dup(key):
            continue
        return name, glist
    return None


def worker(w):
    while not (OUT / 'STOP').exists():
        with lock:
            t = next_trial()
            if t:
                running.add(t[0])
        if not t:
            time.sleep(10)
            continue
        try:
            run_trial(t[0], t[1], w)
        except Exception as e:
            print(json.dumps({'name': t[0], 'status': 'daemon-error', 'error': repr(e)[:300]}), flush=True)
        finally:
            with lock:
                running.discard(t[0])


if __name__ == '__main__':
    ths = [threading.Thread(target=worker, args=(i,)) for i in range(NPAR)]
    for t in ths:
        t.start()
    for t in ths:
        t.join()
