#!/usr/bin/env python3
"""Lane w12a14-cto-hillclimb: automated source hill-climb over admin_cto.rs.

Variants = base text + ordered gene ids (exact, newline-count-preserving substitutions, so every
error-site line stays put). Each variant builds through measure.sh (identity recipe, shared
10-slot lock, score.py vs the landed baseline), at most HC_PAR (default 2) at once.

  hc12.py run   <genes.py> <set> [<set> ...]        set = comma-separated gene ids ('' = base)
  hc12.py screen <genes.py> <baseset> <g1,g2,...>    baseset + each gene alone
  hc12.py show [N]                                   best results
Fitness for landing: zero normalized/raw losses, admin_cto bytes == 27400, ratio > main.
"""
import json, os, subprocess, sys, shutil, hashlib, importlib.util, threading, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

LANE = 'w12a14-cto-hillclimb'
SWARM = Path(os.environ.get('PUMP_SWARM', str(Path(__file__).resolve().parents[6])))  # .../pump-main-swarm
WT = SWARM / 'worktrees' / LANE
OUT = Path.home() / '.cache/pumpfun-reconstruction/lanes' / LANE
MEASURE = SWARM / 'w11/tools/measure.sh'
REL = 'src/creator/admin_cto.rs'
BASEFILE = Path(os.environ.get('HC_BASE', str(WT / 'programs/pump' / REL)))
RES = OUT / 'hc/results.jsonl'
ORIG = 27400
MAIN_RATIO = float(os.environ.get('HC_MAIN_RATIO', '0.43919'))
NWORK = int(os.environ.get('HC_PAR', '2'))
MAINREV = os.environ.get('HC_MAIN', '20a1ae9')
LEDGER = WT / 'reconstruction/pump-main/log_attempt.py'
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
        if g not in genes:
            raise ValueError(f'unknown gene {g}')
        for old, new in genes[g]:
            assert old.count('\n') == new.count('\n'), (g, 'line count')
            n = text.count(old)
            if n != 1:
                raise ValueError(f'gene {g}: old occurs {n}x: {old[:70]!r}')
            text = text.replace(old, new)
    return text


def vid_of(text):
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def done_ids():
    d = {}
    if RES.exists():
        for l in RES.read_text().splitlines():
            if l.strip():
                r = json.loads(l); d[r['vid']] = r
    return d


def best_ratio_exact():
    b = MAIN_RATIO
    for r in done_ids().values():
        if ok(r) and r['bytes'] == ORIG:
            b = max(b, r['ratio'])
    return b


def ok(r):
    return r.get('status') == 'built' and not r.get('losses') and not r.get('raw_losses')


def build(text, label):
    vid = vid_of(text)
    prev = done_ids()
    if vid in prev:
        r = dict(prev[vid]); r['label_dup'] = label; return r
    with lock:
        w = workq.pop(0)
    src = OUT / 'var' / vid
    o = OUT / 't' / vid
    try:
        if src.exists(): shutil.rmtree(src)
        src.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['rsync', '-a', '--exclude', 'target', str(WT / 'programs/pump') + '/', str(src) + '/'], check=True)
        (src / REL).write_text(text)
        t0 = time.time()
        p = subprocess.run(['bash', str(MEASURE), str(src), str(OUT / f'work{w}'), str(o)], capture_output=True, text=True,
                           env=dict(os.environ, PUMP_BUILD_SLOTS='10'))
        r = {'vid': vid, 'label': label, 'secs': round(time.time() - t0), 'main': MAINREV}
        try:
            m = json.loads(p.stdout.strip().splitlines()[-1])
        except Exception:
            m = {'ok': False, 'error': (p.stdout + p.stderr)[-800:]}
        if not m.get('ok'):
            (OUT / 'hc/fail').mkdir(parents=True, exist_ok=True)
            for n in ('build.log', 'build.err', 'build.json'):
                if (o / n).exists(): shutil.copy(o / n, OUT / 'hc/fail' / f'{vid}.{n}')
            log = (o / 'build.log').read_text(errors='replace') if (o / 'build.log').exists() else str(m.get('error'))
            errs = [l for l in log.splitlines() if l.startswith('error')][:3]
            r.update(status='compile-failed', err=errs or [str(m.get('error'))[-300:]])
        else:
            c = m['admin_cto']
            r.update(status='built', bytes=c['cand_bytes'], ratio=c['ratio'], slots_diff=c.get('slots_diff'),
                     calls=c.get('calls_candidate'), norm=m['normalized'], raw=m['raw'], losses=m['losses'],
                     raw_losses=m['raw_losses'][:5], n_raw_losses=len(m['raw_losses']), gains=m['gains'][:20],
                     raw_gains=m['raw_gains'][:5], n_raw_gains=len(m['raw_gains']), sha=m['sha'],
                     hop=m.get('swap_hop', {}).get('ratio'))
            try:
                fm = subprocess.run([sys.executable, str(OUT / 'hc/framemap.py'), str(o / 'unstripped.so'), '--summary'],
                                    capture_output=True, text=True, timeout=120)
                r['frame'] = json.loads(fm.stdout.strip().splitlines()[-1])
            except Exception as e:
                r['frame'] = {'err': repr(e)[:100]}
        (OUT / 'hc/texts').mkdir(parents=True, exist_ok=True)
        (OUT / 'hc/texts' / f'{vid}.rs').write_text(text)
        keep = ok(r) and r['bytes'] == ORIG and r['ratio'] > MAIN_RATIO
        with lock:
            with RES.open('a') as f: f.write(json.dumps(r) + '\n')
        if keep:
            (OUT / 'hc/keep' / vid).mkdir(parents=True, exist_ok=True)
            for n in ('unstripped.so', 'candidate.so', 'score.json', 'cto.json'):
                if (o / n).exists(): shutil.copy(o / n, OUT / 'hc/keep' / vid / n)
        shutil.rmtree(o, ignore_errors=True)
        ledger(r)
        return r
    finally:
        shutil.rmtree(src, ignore_errors=True)
        with lock:
            workq.append(w)


def ledger(r):
    key = None
    for v in range(1, 6):
        k = f"0x22a10-w12-{MAINREV}-hc-{r['vid']}-v{v}"
        c = subprocess.run([sys.executable, str(LEDGER), 'check', '--dedupe-key', k], capture_output=True, text=True)
        try:
            dup = json.loads(c.stdout.strip().splitlines()[-1]).get('duplicate')
        except Exception:
            dup = True
        if dup is False:
            key = k; break
    if key is None:
        return
    st = r['status']
    if st == 'built':
        st = 'partial' if (ok(r) and r['bytes'] == ORIG and r['ratio'] > MAIN_RATIO) else 'rejected'
    data = {'output': str(OUT / 'hc/texts' / (r['vid'] + '.rs')), 'normalized': r.get('norm'), 'raw': r.get('raw'),
            'losses': r.get('losses'), 'raw_losses': (r.get('raw_losses') or [])[:5], 'n_raw_losses': len(r.get('raw_losses') or []),
            'target': {'ratio': r.get('ratio'), 'slots_diff': r.get('slots_diff'), 'cand_bytes': r.get('bytes')},
            'notes': f"genes [{r['label']}] on main {MAINREV}; calls {r.get('calls')}; err {r.get('err')}"}
    subprocess.run([sys.executable, str(LEDGER), 'record', '--lane', LANE, '--approach', 'mutation-hillclimb',
                    '--target', '0x22a10', '--dedupe-key', key, '--hypothesis',
                    f"hill-climb variant genes [{r['label']}] on main {MAINREV}",
                    '--status', st, '--data', json.dumps(data)], capture_output=True)


def fmt(r):
    return (f"{r.get('vid')} {str(r.get('status'))[:6]:6} {str(r.get('bytes','')):>6} {str(r.get('ratio','')):<8} "
            f"s{r.get('slots_diff')} n{r.get('norm')}/{r.get('raw')} L{len(r.get('losses') or [])}/{len(r.get('raw_losses') or [])} "
            f"{r.get('secs')}s fr{(r.get('frame') or {}).get('r10_equal')}/{(r.get('frame') or {}).get('first_div_T')} [{r.get('label')}] {r.get('err') or ''}")


def run_jobs(jobs):
    from concurrent.futures import as_completed
    out = []
    with ThreadPoolExecutor(NWORK) as ex:
        futs = [ex.submit(build, *j) for j in jobs]
        for f in as_completed(futs):
            try:
                r = f.result()
            except Exception as e:
                print('JOBERR', repr(e)[:300], flush=True); continue
            print(fmt(r), flush=True); out.append(r)
    return out


def mk_jobs(genes, sets):
    base = BASEFILE.read_text()
    jobs = []
    seen = set()
    for s in sets:
        ids = [x for x in s.split(',') if x]
        try:
            t = apply(base, genes, ids)
        except Exception as e:
            print('SKIP', s, e, flush=True); continue
        v = vid_of(t)
        if v in seen:
            print('SAME', s, v, flush=True); continue
        seen.add(v)
        jobs.append((t, s))
    return jobs


def show(n=40):
    rows = [r for r in done_ids().values()]
    ex = sorted([r for r in rows if ok(r) and r['bytes'] == ORIG], key=lambda r: -r['ratio'])
    print('== exact 27400, zero-loss, by ratio')
    for r in ex[:n]: print(fmt(r))
    an = sorted([r for r in rows if r.get('status') == 'built' and not r.get('losses')], key=lambda r: -r['ratio'])
    print('== any size, zero normalized loss, by ratio')
    for r in an[:n]: print(fmt(r))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'run':
        g = load_genes(sys.argv[2]); run_jobs(mk_jobs(g, sys.argv[3:]))
    elif cmd == 'screen':
        g = load_genes(sys.argv[2]); bs = sys.argv[3]; pool = [x for x in sys.argv[4].split(',') if x]
        pre = [x for x in bs.split(',') if x]
        sets = [bs] + [','.join(pre + [x]) for x in pool if x not in pre]
        run_jobs(mk_jobs(g, sets))
    elif cmd == 'check':
        g = load_genes(sys.argv[2]); base = BASEFILE.read_text()
        for s in sys.argv[3:]:
            ids = [x for x in s.split(',') if x]
            try:
                t = apply(base, g, ids); print('OK', vid_of(t), s)
            except Exception as e:
                print('FAIL', s, e)
    elif cmd == 'daemon':
        pass
    else:
        show(int(sys.argv[2]) if len(sys.argv) > 2 else 40)


def daemon(genes_path, qfile, idle_exit=900):
    """Two (HC_PAR) workers pop sets from qfile (one per line, first line first); genes reload each pop.
    Edit qfile any time (prepend urgent sets). Exits after idle_exit seconds with an empty queue."""
    import fcntl
    qf = Path(qfile)
    def pop():
        with open(str(qf) + '.lock', 'w') as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            lines = [l.strip() for l in qf.read_text().splitlines()] if qf.exists() else []
            while lines and (not lines[0] or lines[0].startswith('#')):
                lines.pop(0)
            if not lines:
                return None
            s = lines.pop(0)
            qf.write_text('\n'.join(lines) + ('\n' if lines else ''))
            return s
    def worker():
        idle = 0
        while True:
            s = pop()
            if s is None:
                if idle > idle_exit: return
                time.sleep(5); idle += 5; continue
            idle = 0
            try:
                g = load_genes(genes_path)
                ids = [x for x in s.split(',') if x and x != 'BASE']
                t = apply(BASEFILE.read_text(), g, ids)
            except Exception as e:
                print('SKIP', s, repr(e)[:200], flush=True); continue
            try:
                r = build(t, s)
                print(fmt(r), flush=True)
            except Exception as e:
                print('JOBERR', s, repr(e)[:300], flush=True)
    ths = [threading.Thread(target=worker) for _ in range(NWORK)]
    for th in ths: th.start()
    for th in ths: th.join()


if __name__ == '__main__' and sys.argv[1] == 'daemon':
    daemon(sys.argv[2], sys.argv[3])
