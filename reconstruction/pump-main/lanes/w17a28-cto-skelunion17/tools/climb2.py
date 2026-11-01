#!/usr/bin/env python3
"""climb2.py <m.ll> <out.jsonl> [--init f1,f2..] [--K 40] [--R 6] [--E 4] [--at 27400]
Re-voting greedy sticky RA climb with the private RAPRIO llc (experiment only; a bound on register naming):
each epoch re-tags the asm under the current forces, re-votes (rvote.py) and runs up to R greedy rounds over the
top-K new vote genes. Stops when an epoch adds nothing. Reports the best M overall and the best M at exactly --at bytes."""
import sys, os, json, subprocess, multiprocessing as mp
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import lx, rvote
OUT = os.path.dirname(T)
M_LL = None
def init(m):
    global M_LL; M_LL = m
def run(forces):
    env = dict(os.environ, RAPRIO_STICKY='1', RAPRIO_FORCE=','.join(forces))
    name = 'climb2/' + str(abs(hash((M_LL,) + tuple(forces))))[:14]
    r = lx.run(M_LL, name, 'p', env=env)
    try: os.remove(OUT + '/lx/' + name + '/fn.bin')
    except Exception: pass
    return {'forces': forces, 'M': r.get('M'), 'bytes': r.get('bytes'), 'err': r.get('err')}
def votes(m, forces, tag):
    d = f'{OUT}/lx/climb2v'; os.makedirs(d, exist_ok=True)
    env = dict(os.environ, RAPRIO_STICKY='1', RAPRIO_FORCE=','.join(forces), RAPRIO_TAG='1')
    s = f'{d}/{tag}.s'
    subprocess.run([T + '/llcp.sh', m, '-o', s], env=env, capture_output=True)
    r = lx.run(m, f'climb2v/{tag}', 'p', env=dict(os.environ, RAPRIO_STICKY='1', RAPRIO_FORCE=','.join(forces)))
    return rvote.run(s, f'{OUT}/lx/climb2v/{tag}/fn.bin')
if __name__ == '__main__':
    a = sys.argv[1:]; m, of = a[0], a[1]
    def opt(k, d):
        return a[a.index(k) + 1] if k in a else d
    cur = [x for x in opt('--init', '').split(',') if x]
    K = int(opt('--K', 40)); R = int(opt('--R', 6)); E = int(opt('--E', 4)); AT = int(opt('--at', 27400))
    init(m); best = run(cur); out = open(of, 'a')
    bestat = best if best['bytes'] == AT else None
    print(json.dumps({'start': best}), flush=True)
    tagn = os.path.basename(os.path.dirname(m))
    with mp.Pool(4, initializer=init, initargs=(m,)) as p:
        for ep in range(E):
            V = votes(m, cur, f'{tagn}_e{ep}')
            vs = [x for x in V if x['v'] not in {int(f.split('=')[0]) for f in cur}][:K]
            genes = ['%d=%s' % (x['v'], x['want']) for x in vs]
            added = 0
            for rd in range(R):
                tr = [g for g in genes if g not in cur]
                if not tr: break
                res = list(p.imap(run, [cur + [g] for g in tr]))
                for x in res:
                    out.write(json.dumps(x) + '\n')
                    if x.get('M') and x['bytes'] == AT and (bestat is None or x['M'] > bestat['M']):
                        bestat = x
                ok = [(x, g) for x, g in zip(res, tr) if x.get('M')]
                if not ok: break
                x, g = max(ok, key=lambda t: t[0]['M'])
                if x['M'] <= best['M']: break
                cur.append(g); best = x; added += 1
                print(json.dumps({'epoch': ep, 'round': rd, 'M': x['M'], 'bytes': x['bytes'], 'n': len(cur)}), flush=True)
            if not added: break
    print(json.dumps({'final': best, 'best_at': bestat}), flush=True)
