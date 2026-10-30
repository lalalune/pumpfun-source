#!/usr/bin/env python3
"""Automated hill-climb over admin_cto.rs source mutations (lane w10r1-admincto-hillclimb).

Each gene is a list of exact (old, new) substitutions that keep the file's line count and
every error-site line. A variant = base text + an ordered gene set. Variants build in parallel
(own fastbuild work dirs, the shared 10-slot lock still applies), then target_metric + score.py
(against the lane baseline score.json) decide fitness:
  key = (calls equal?, |bytes-27400|, -ratio), only zero-loss variants qualify.

  hc.py run  <genes.py> <gene-set>[ <gene-set> ...]   # gene-set = comma-separated gene ids ('' = base)
  hc.py show                                          # table of results
"""
import json, os, subprocess, sys, shutil, hashlib, importlib.util, threading, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

WT = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w10r1-admincto-hillclimb')
OUT = Path.home() / '.cache/pumpfun-reconstruction/lanes/w10r1-admincto-hillclimb'
H = WT / 'reconstruction/harness'
REL = 'src/creator/admin_cto.rs'
BASEFILE = Path(os.environ.get('HC_BASE', str(WT / 'programs/pump' / REL)))
BASESCORE = OUT / 'out/base/score.json'
RES = OUT / 'hc/results.jsonl'
ORIG = 27400
NWORK = int(os.environ.get('HC_PAR', '2'))
LANE = 'w10r1-admincto-hillclimb'
MAINREV = os.environ.get('HC_MAIN', '917ee615')
lock = threading.Lock()
workq = list(range(NWORK))


def load_genes(p):
    spec = importlib.util.spec_from_file_location('genes', p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.GENES


def apply(text, genes, ids):
    for g in ids:
        if not g:
            continue
        for old, new in genes[g]:
            assert old.count('\n') == new.count('\n'), (g, 'line count')
            n = text.count(old)
            if n != 1:
                raise ValueError(f'gene {g}: old occurs {n}x: {old[:60]!r}')
            text = text.replace(old, new)
    return text


def vid_of(text):
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def done_ids():
    d = {}
    if RES.exists():
        for l in RES.read_text().splitlines():
            r = json.loads(l); d[r['vid']] = r
    return d


def build(text, label):
    vid = vid_of(text)
    prev = done_ids()
    if vid in prev:
        r = dict(prev[vid]); r['label_dup'] = label; return r
    with lock:
        w = workq.pop(0)
    src = OUT / 'hc/src' / vid
    try:
        if src.exists(): shutil.rmtree(src)
        src.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['cp', '-c', '-R', str(WT / 'programs/pump'), str(src)], check=True)
        (src / REL).write_text(text)
        o = OUT / 'hc/out' / vid
        env = dict(os.environ, PUMP_BUILD_SLOTS='10')
        t0 = time.time()
        p = subprocess.run([sys.executable, str(H / 'fastbuild.py'), '--src', str(src), '--work', str(OUT / f'work{w}'), '--out', str(o)],
                           capture_output=True, text=True, env=env)
        r = {'vid': vid, 'label': label, 'secs': round(time.time() - t0)}
        so = o / 'unstripped.so'
        if p.returncode != 0 or not so.exists():
            log = (o / 'build.log').read_text(errors='replace') if (o / 'build.log').exists() else p.stdout + p.stderr
            errs = [l for l in log.splitlines() if l.startswith('error')][:3]
            r.update(status='compile-failed', err=errs)
        else:
            m = json.loads(subprocess.run([sys.executable, str(H / 'target_metric.py'), str(so), '0x22a10', '--sym', 'admin_cto::execute$', '--slots', '400'], capture_output=True, text=True).stdout)
            s = json.loads(subprocess.run([sys.executable, str(H / 'score.py'), str(so), '--baseline', str(BASESCORE), '--quiet'], capture_output=True, text=True).stdout)
            r.update(status='built', bytes=m['cand_bytes'], ratio=m['ratio'], calls=m['calls_candidate'],
                     slots_diff=m.get('slots_diff'), norm=s['normalized'], raw=s['raw'], losses=s['losses'], raw_losses=s['raw_losses'],
                     gains=s['gains'], raw_gains=s['raw_gains'], sha=hashlib.sha256(so.read_bytes()).hexdigest()[:16])
            keep = OUT / 'hc/keep' / vid
            if r['losses'] == [] and r['raw_losses'] == []:
                keep.mkdir(parents=True, exist_ok=True)
                shutil.copy(so, keep / 'unstripped.so')
            (OUT / 'hc/texts').mkdir(parents=True, exist_ok=True)
        (OUT / 'hc/texts').mkdir(parents=True, exist_ok=True)
        (OUT / 'hc/texts' / f'{vid}.rs').write_text(text)
        with lock:
            with RES.open('a') as f: f.write(json.dumps(r) + '\n')
        shutil.rmtree(o, ignore_errors=True)
        ledger(r)
        return r
    finally:
        shutil.rmtree(src, ignore_errors=True)
        with lock:
            workq.append(w)


def ledger(r):
    key = f"0x22a10-main-{MAINREV}-hc-{r['vid']}-v1"
    st = r['status']
    if st == 'built':
        st = 'partial' if fit(r) < fit(BASE_R or r) else 'rejected'
    data = {k: r.get(k) for k in ('vid', 'bytes', 'ratio', 'calls', 'norm', 'raw', 'losses', 'raw_losses', 'err', 'sha')}
    data['output'] = str(OUT / 'hc/texts' / (r['vid'] + '.rs'))
    subprocess.run([sys.executable, str(WT / 'reconstruction/pump-main/log_attempt.py'), 'record', '--lane', LANE, '--approach', 'mutation-hillclimb',
                    '--target', '0x22a10', '--dedupe-key', key, '--hypothesis', f"hill-climb variant genes [{r['label']}] on main {MAINREV}",
                    '--status', st, '--data', json.dumps(data)], capture_output=True)


BASE_R = None


def fit(r):
    if r.get('status') != 'built' or r['losses'] or r['raw_losses']:
        return (9, 0, 0)
    return (0 if r['calls'] == [154, 3] else 1, abs(r['bytes'] - ORIG), -r['ratio'])


def run(genes_path, sets):
    global BASE_R
    genes = load_genes(genes_path)
    base = BASEFILE.read_text()
    jobs = []
    for s in sets:
        ids = [x for x in s.split(',') if x]
        try:
            jobs.append((apply(base, genes, ids), s))
        except Exception as e:
            print('SKIP', s, e)
    d = done_ids(); BASE_R = d.get(vid_of(base))
    with ThreadPoolExecutor(NWORK) as ex:
        for r in ex.map(lambda j: build(*j), jobs):
            print(json.dumps({k: r.get(k) for k in ('label', 'label_dup', 'vid', 'status', 'bytes', 'ratio', 'calls', 'losses', 'raw_losses', 'err')}), flush=True)


def show():
    rows = list(done_ids().values())
    rows.sort(key=fit)
    for r in rows:
        print(f"{r['vid']} {r['status'][:6]:6} {r.get('bytes',''):>6} {r.get('ratio',''):<8} {str(r.get('calls','')):10} L{len(r.get('losses') or [])}/{len(r.get('raw_losses') or [])} G{len(r.get('gains') or [])}/{len(r.get('raw_gains') or [])} {r['label'][:110]}")


if __name__ == '__main__':
    if sys.argv[1] == 'run':
        run(sys.argv[2], sys.argv[3:])
    else:
        show()
