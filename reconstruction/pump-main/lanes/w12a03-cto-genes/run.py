#!/usr/bin/env python3
"""Build and score admin_cto gene trials (lane w12a03-cto-genes).

  run.py <trial> [<trial> ...]        trial = name=gene1+gene2+... ('name=' alone = main source)
  run.py --file trials.txt            one trial per line

Each trial copies programs/pump (rsync --exclude target) into $OUT/var/<name>, applies the genes from
genes.py to admin_cto.rs, runs measure.sh with one of two lane work dirs, appends a row to
$OUT/results.jsonl and records it in the shared ledger (dedupe key 0x22a10-w12-<main7>-gene-<name>-v1).
Binaries are deleted afterwards unless the trial is a zero-loss improvement at 27,400 B.
"""
import json, os, subprocess, sys, threading, shutil, time, difflib, importlib.util
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

LANE = 'w12a03-cto-genes'
SWARM = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm')
WT = SWARM / 'worktrees' / LANE
OUT = Path.home() / '.cache/pumpfun-reconstruction/lanes' / LANE
TOOLS = SWARM / 'w11/tools'
LEDGER = WT / 'reconstruction/pump-main/log_attempt.py'
REL = 'src/creator/admin_cto.rs'
MAIN7 = os.environ.get('GENE_MAIN7', '20a1ae9')
BASE = {'ratio': 0.43919, 'bytes': 27400, 'slots': 3352}
NPAR = int(os.environ.get('GENE_PAR', '2'))
RES = Path(os.environ.get('GENE_RES', str(OUT / 'results.jsonl')))
BASEFILE = Path(os.environ.get('GENE_BASEFILE', str(WT / 'programs/pump' / REL)))

spec = importlib.util.spec_from_file_location('genes', str(Path(__file__).resolve().parent / 'genes.py'))
genes = importlib.util.module_from_spec(spec); spec.loader.exec_module(genes)
lock = threading.Lock()
works = list(range(NPAR))


def done():
    d = {}
    if RES.exists():
        for l in RES.read_text().splitlines():
            if l.strip():
                r = json.loads(l); d[r['name']] = r
    return d


def ledger_exists(key):
    r = subprocess.run(['python3', str(LEDGER), 'check', '--dedupe-key', key], capture_output=True, text=True)
    try:
        return bool(json.loads(r.stdout.strip().splitlines()[-1]).get('duplicate'))
    except Exception:
        return False


def run_trial(name, glist):
    key = f'0x22a10-w12-{MAIN7}-gene-{name}-v1'
    if ledger_exists(key):
        print(json.dumps({'name': name, 'status': 'skipped-ledger-has-key', 'key': key}), flush=True)
        return None
    base = BASEFILE.read_text()
    try:
        text = genes.apply(base, glist)
    except ValueError as e:
        row = {'name': name, 'genes': glist, 'status': 'apply-failed', 'error': str(e)}
        with lock:
            RES.open('a').write(json.dumps(row) + '\n')
        return row
    var = OUT / 'var' / name
    if var.exists():
        shutil.rmtree(var)
    var.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['rsync', '-a', '--exclude', 'target', f'{WT}/programs/pump/', f'{var}/'], check=True)
    (var / REL).write_text(text)
    with lock:
        w = works.pop()
    t0 = time.time()
    try:
        tout = OUT / 't' / name
        r = subprocess.run([str(TOOLS / 'measure.sh'), str(var), str(OUT / f'work{w}'), str(tout)], capture_output=True, text=True)
    finally:
        with lock:
            works.append(w)
    secs = int(time.time() - t0)
    line = (r.stdout.strip().splitlines() or ['{}'])[-1]
    try:
        m = json.loads(line)
    except Exception:
        m = {'ok': False, 'error': r.stdout[-800:] + r.stderr[-800:]}
    diff = ''.join(difflib.unified_diff(base.splitlines(True), text.splitlines(True), 'main/admin_cto.rs', f'{name}/admin_cto.rs', n=0))
    row = {'name': name, 'genes': glist, 'secs': secs, 'key': key}
    if not m.get('ok'):
        row.update(status='compile-failed', error=str(m.get('error', ''))[-600:])
    else:
        c = m.get('admin_cto') or {}
        row.update(ratio=c.get('ratio'), bytes=c.get('cand_bytes'), slots=c.get('slots_diff'), calls=c.get('calls_candidate'),
                   normalized=m['normalized'], raw=m['raw'], losses=m['losses'], raw_losses_n=len(m['raw_losses']),
                   raw_losses=m['raw_losses'][:5], gains=m['gains'], raw_gains=m['raw_gains'][:5], sha=m['sha'],
                   hop=m.get('swap_hop'), out=m['out'])
        row['d_bytes'] = (row['bytes'] or 0) - BASE['bytes']
        row['d_ratio'] = round((row['ratio'] or 0) - BASE['ratio'], 5)
        zero = not m['losses'] and not m['raw_losses']
        better = zero and row['bytes'] == 27400 and (row['ratio'] or 0) > BASE['ratio']
        row['status'] = 'partial' if better else 'built'
        if not better:
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
    subprocess.run(['python3', str(LEDGER), 'record', '--lane', LANE, '--approach', 'gene-harvest', '--target', '0x22a10', '--dedupe-key', key,
                    '--hypothesis', f'gene {"+".join(glist) or "main"} alone/combined on main {MAIN7}: ' + '; '.join(genes.SRC.get(g, '?') for g in glist)[:400],
                    '--status', row['status'] if row['status'] != 'apply-failed' else 'analyzed', '--data', json.dumps(data)], capture_output=True, text=True)
    shutil.rmtree(var, ignore_errors=True)
    print(json.dumps({k: row.get(k) for k in ('name', 'status', 'bytes', 'd_bytes', 'ratio', 'd_ratio', 'slots', 'normalized', 'raw', 'raw_losses_n', 'secs')}), flush=True)
    return row


def main():
    args = sys.argv[1:]
    if args and args[0] == '--file':
        args = [l.strip() for l in Path(args[1]).read_text().splitlines() if l.strip() and not l.startswith('#')]
    have = done()
    todo = []
    for a in args:
        name, _, gs = a.partition('=')
        glist = [g for g in gs.split('+') if g]
        if name in have and have[name].get('status') not in ('compile-failed',):
            continue
        for g in glist:
            if g not in genes.G:
                sys.exit(f'unknown gene {g}')
        todo.append((name, glist))
    with ThreadPoolExecutor(NPAR) as ex:
        list(ex.map(lambda t: run_trial(*t), todo))


if __name__ == '__main__':
    main()
