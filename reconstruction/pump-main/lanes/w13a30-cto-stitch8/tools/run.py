#!/usr/bin/env python3
"""Background variant runner for lane w13a11-cto-stitch.

run.py <queue> <results.jsonl> [workers]
Queue lines: "<name> <base-file> gene1 gene2 ..." (append lines while it runs; '#' comments).
Each variant: copy programs/pump (rsync --exclude target), write admin_cto.rs = genes applied to
base, fastbuild (shared 10-slot lock), target_metric on admin_cto. One JSON line per variant.
Stops when <queue>.stop exists, or when the queue is drained and <queue>.drain exists.
"""
import hashlib, importlib, json, os, subprocess, sys, threading, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genes30 as GN

OUT = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w13a30-cto-stitch8')
WT = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a30-cto-stitch8'
H = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness'
KEEP_RATIO = 0.56291
queue, results = sys.argv[1], sys.argv[2]
workers = int(sys.argv[3]) if len(sys.argv) > 3 else 2
lock = threading.Lock()
taken = set()


def done_names():
    s = {}
    if os.path.exists(results):
        for ln in open(results):
            try:
                d = json.loads(ln)
                s[d['name']] = d
            except Exception:
                pass
    return s


def next_item():
    with lock:
        done = done_names()
        for ln in open(queue):
            ln = ln.strip()
            if not ln or ln.startswith('#'):
                continue
            parts = ln.split()
            if parts[0] in done or parts[0] in taken:
                continue
            taken.add(parts[0])
            return parts
    return None


def run_one(parts, slot):
    name, base, gl = parts[0], parts[1], parts[2:]
    t0 = time.time()
    rec = {'name': name, 'base': os.path.basename(base), 'genes': gl}
    try:
        with lock:
            importlib.reload(GN)
        src = open(base).read()
        text = GN.apply(gl, src)
    except Exception as e:
        rec.update(status='edit-fail', error=str(e)[:300])
        return rec
    sha = hashlib.sha256(text.encode()).hexdigest()[:16]
    rec['text_sha'] = sha
    with lock:
        for d in done_names().values():
            if d.get('text_sha') == sha and d.get('status') == 'built':
                rec.update({k: d[k] for k in ('bytes', 'ratio', 'slots_diff', 'calls', 'so_sha') if k in d})
                rec.update(status='built', dup_of=d['name'], secs=0)
                return rec
    var = f'{OUT}/var/{name}'
    os.makedirs(var, exist_ok=True)
    subprocess.run(['rsync', '-a', '--delete', '--exclude', 'target', f'{WT}/programs/pump/', var + '/'], check=True)
    open(f'{var}/src/creator/admin_cto.rs', 'w').write(text)
    tdir = f'{OUT}/t/{name}'
    os.makedirs(tdir, exist_ok=True)
    env = dict(os.environ, PUMP_BUILD_SLOTS='10')
    b = subprocess.run(['python3', f'{H}/fastbuild.py', '--src', var, '--work', f'{OUT}/work{slot}', '--out', tdir],
                       capture_output=True, text=True, env=env)
    open(f'{tdir}/build.out', 'w').write(b.stdout[-20000:] + '\n---\n' + b.stderr[-20000:])
    so = f'{tdir}/unstripped.so'
    if b.returncode != 0 or not os.path.exists(so):
        rec.update(status='compile-failed', secs=round(time.time() - t0), error=(b.stderr or b.stdout)[-600:])
        subprocess.run(['rm', '-rf', var])
        return rec
    m = subprocess.run(['python3', f'{H}/target_metric.py', so, '0x22a10', '--sym', 'admin_cto::execute$', '--slots', '4000'],
                       capture_output=True, text=True)
    try:
        d = json.loads(m.stdout.strip().splitlines()[0])
    except Exception:
        d = {}
    rec.update(status='built', bytes=d.get('cand_bytes'), ratio=d.get('ratio'), slots_diff=d.get('slots_diff'),
               calls=d.get('calls_candidate'), secs=round(time.time() - t0),
               so_sha=hashlib.sha256(open(so, 'rb').read()).hexdigest()[:16])
    open(f'{tdir}/admin_cto.rs', 'w').write(text)
    if not (rec['bytes'] == 27400 and (rec['ratio'] or 0) > KEEP_RATIO):
        for f in ('unstripped.so', 'candidate.so'):
            try:
                os.remove(f'{tdir}/{f}')
            except FileNotFoundError:
                pass
    subprocess.run(['rm', '-rf', var])
    return rec


def worker(slot):
    while True:
        if os.path.exists(queue + '.stop'):
            return
        if slot > 0 and not os.path.exists(f'{queue}.w{slot}'):
            time.sleep(5)
            continue
        it = next_item()
        if it is None:
            if os.path.exists(queue + '.drain'):
                return
            time.sleep(5)
            continue
        rec = run_one(it, slot)
        with lock:
            with open(results, 'a') as f:
                f.write(json.dumps(rec) + '\n')
        print(json.dumps(rec), flush=True)


ts = [threading.Thread(target=worker, args=(i,)) for i in range(workers)]
for t in ts:
    t.start()
for t in ts:
    t.join()
