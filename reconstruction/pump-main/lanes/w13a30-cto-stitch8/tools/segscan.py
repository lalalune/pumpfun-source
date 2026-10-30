#!/usr/bin/env python3
"""segscan.py: llc oracle over AccountInfo clone field placement in admin_cto::execute (experiment only).

Every AccountInfo clone in execute (inlined `clone()` or a hand-written `AccountInfo{..}` literal) has two Rc
increments (lamports at +8, data at +16). A plain field (key +0, owner +24, rent_epoch +32, is_signer +40,
is_writable +41, executable +42) is loaded in one of three segments: S0 before the first Rc, S1 between, S2 after
the second Rc. A move `c<i>:<f><seg>` puts field f of clone i at the end of S0/S1 or the start of S2. The matching
source is the literal with fields in the resulting order (see `order`).

  segscan.py list <mod.ll>                   clones with base, account offset and current order
  segscan.py scan <mod.ll> <out> [--moves m1,m2] [--j 4]   all single moves on top of the given moves
  segscan.py greedy <mod.ll> <out> [--rounds N] [--j 4]    greedy at 27,400 B
"""
import sys, os, re, json, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.environ.get("CTORACLE_DIR", "/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a21-cto-clonefeat/reconstruction/pump-main/lanes/w13a21-cto-clonefeat/scripts")  
sys.path.insert(0, S)
import ctoracle as co
FOFF = {'k': 0, 'o': 24, 'r': 32, 's': 40, 'w': 41, 'e': 42}
OFFF = {v: k for k, v in FOFF.items()}


def split(txt):
    sym = co.SYMRE.search(txt).group(0); i, j = co.fn_bounds(txt, sym)
    return txt[:i], txt[i:j].split('\n'), txt[j:]


def defn(L, n):
    m = re.match(r'  %(\S+) = ', L[n]); return m.group(1) if m else None


def clones(L):
    """find clones: base X with an Rc increment at +8 and +16 (gep, load ptr, load i64, add 1, store)."""
    out = []
    geps = {}
    for n, l in enumerate(L):
        m = re.match(r'  %(\S+) = getelementptr inbounds i8, ptr %(\S+), i64 (\d+)$', l)
        if m: geps.setdefault(m.group(2), []).append((n, int(m.group(3)), m.group(1)))
    for X, gl in geps.items():
        d = {o: (n, v) for n, o, v in gl}
        if 8 not in d or 16 not in d: continue
        # Rc check: gep8 followed by load ptr then load i64 and add 1
        def isrc(n):
            return n + 4 < len(L) and re.match(r'  %\S+ = load ptr, ptr %' + re.escape(d_name(L, n)) + ',', L[n + 1]) and 'load i64' in L[n + 2]
        if not (isrc(d[8][0]) and isrc(d[16][0])): continue
        f = {}
        for o in (24, 32, 40, 41, 42):
            if o in d:
                n = d[o][0]
                if n + 1 < len(L) and re.match(r'  %\S+ = load \S+, ptr %' + re.escape(d[o][1]) + ',', L[n + 1]):
                    f[OFFF[o]] = (n, n + 1)
        kl = [n for n, l in enumerate(L) if re.match(r'  %\S+ = load ptr, ptr %' + re.escape(X) + r', align 8', l)]
        kl = [n for n in kl if abs(n - d[8][0]) < 80]
        if kl: f['k'] = (None, kl[0])
        if len(f) < 6: continue
        out.append({'X': X, 'r8': d[8][0], 'r16': d[16][0], 'f': f})
    out.sort(key=lambda c: min(c['r8'], c['r16']))
    return out


def d_name(L, n):
    return defn(L, n)


def seg_of(c, n):
    a, b = sorted((c['r8'], c['r16']))
    return 0 if n < a else (1 if n < b else 2)


def exit_line(L, rn):
    """index of the first instruction of the block after the Rc at gep line rn (skips the trap block)."""
    n = rn; labs = 0
    while n < len(L):
        n += 1
        if re.match(r'^\S.*:\s*(;.*)?$', L[n]):
            labs += 1
            if labs == 2: return n + 1
    raise ValueError('no exit')


def order(L, c):
    pos = []
    for k, (g, ld) in c['f'].items(): pos.append((ld, k))
    pos.append((c['r8'], 'l')); pos.append((c['r16'], 'd'))
    return ''.join(k for _, k in sorted(pos))


def apply(fn_lines, moves):
    """moves: list of 'c<i>:<f><seg>' applied in order; clones re-detected after each move."""
    L = list(fn_lines)
    for mv in moves:
        cs = clones(L)
        m = re.match(r'c(\d+):([korswe])([012])$', mv); i, f, sg = int(m.group(1)), m.group(2), int(m.group(3))
        c = cs[i]; g, ld = c['f'][f]
        a, b = sorted((c['r8'], c['r16']))
        lines = [L[x] for x in (g, ld) if x is not None]
        for x in sorted([x for x in (g, ld) if x is not None], reverse=True): L.pop(x)
        cs = clones(L); c = cs[i]; a, b = sorted((c['r8'], c['r16']))
        if sg == 0: t = a
        elif sg == 1: t = b
        else: t = exit_line(L, b)
        L[t:t] = lines
    s = '\n'.join(L)
    order_ = [m.group(1) for m in re.finditer(r'^  %(\d+) = ', s, re.M)]
    mp = dict(zip(order_, sorted(order_, key=int)))
    s = re.sub(r'%(\d+)(?![\w.$-])', lambda m: '%__' + mp[m.group(1)] if m.group(1) in mp else m.group(0), s)
    return s.replace('%__', '%')


def run(mod, moves, out, lab):
    d = f'{out}/{lab}'
    env = dict(os.environ, MOVES=','.join(moves))
    r = subprocess.run([sys.executable, S + '/ctoracle.py', 'run', mod, d] + (['--edit', HERE + '/segedit.py'] if moves else []), capture_output=True, text=True, env=env)
    subprocess.run(['rm', '-rf', d])
    try:
        return json.loads(r.stdout.strip().split('\n')[-1])
    except Exception:
        return {'err': (r.stderr or r.stdout)[-200:]}


def singles(mod, base_moves):
    pre, L, post = split(open(mod).read())
    L2 = apply(L, base_moves).split('\n') if base_moves else L
    cs = clones(L2); res = []
    for i, c in enumerate(cs):
        for f, (g, ld) in c['f'].items():
            cur = seg_of(c, ld)
            for sg in (0, 1, 2):
                if sg != cur: res.append(f'c{i}:{f}{sg}')
    return res


def main():
    a = sys.argv[1:]; cmd = a.pop(0); mod = a.pop(0)
    j = int(a[a.index('--j') + 1]) if '--j' in a else 4
    if cmd == 'list':
        pre, L, post = split(open(mod).read())
        bm = a[a.index('--moves') + 1].split(',') if '--moves' in a else []
        if bm: L = apply(L, bm).split('\n')
        for i, c in enumerate(clones(L)):
            base = [l for l in L if re.match(r'  %' + re.escape(c['X']) + ' = ', l)]
            print(i, c['X'], order(L, c), base[0].strip()[:90] if base else '')
        return
    out = a.pop(0); os.makedirs(out, exist_ok=True)
    base = a[a.index('--moves') + 1].split(',') if '--moves' in a and a[a.index('--moves') + 1] else []
    if cmd == 'scan':
        mv = singles(mod, base)
        with ThreadPoolExecutor(j) as ex:
            rs = list(ex.map(lambda m: (m, run(mod, base + [m], out, m.replace(':', '_'))), mv))
        with open(out + '/scan.jsonl', 'a') as f:
            for m, r in rs: f.write(json.dumps({'base': base, 'move': m, **r}) + '\n')
        ok = [(m, r) for m, r in rs if 'ratio' in r]
        print('runs', len(rs), 'ok', len(ok))
        for m, r in sorted([x for x in ok if x[1]['bytes'] == 27400], key=lambda x: -x[1]['ratio'])[:12]: print('27400', m, r['ratio'])
        for m, r in sorted(ok, key=lambda x: -x[1]['ratio'])[:12]: print('all', m, r['bytes'], r['ratio'])
    elif cmd == 'greedy':
        rounds = int(a[a.index('--rounds') + 1]) if '--rounds' in a else 4
        cur = base; best = run(mod, cur, out, 'base')['ratio']; print('base', best, flush=True)
        for rd in range(rounds):
            mv = singles(mod, cur)
            with ThreadPoolExecutor(j) as ex:
                rs = list(ex.map(lambda m: (m, run(mod, cur + [m], out, f'g{rd}_' + m.replace(':', '_'))), mv))
            with open(out + '/greedy.jsonl', 'a') as f:
                for m, r in rs: f.write(json.dumps({'base': cur, 'move': m, **r}) + '\n')
            ok = sorted([(m, r) for m, r in rs if r.get('bytes') == 27400 and r['ratio'] > best], key=lambda x: -x[1]['ratio'])
            if not ok: print('round', rd, 'no gain'); break
            cur = cur + [ok[0][0]]; best = ok[0][1]['ratio']; print('round', rd, cur, best, flush=True)
        print(json.dumps({'moves': cur, 'ratio': best}))


if __name__ == '__main__':
    main()
