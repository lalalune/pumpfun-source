#!/usr/bin/env python3
"""rf.py <m.ll> <tag> [FORCE=..] [PRIO=..] [STICKY=1] [HINT=..] [NOHINT=..]: private RAPRIO llc on a post-opt slim
module; prints M, ratio, bytes, and per-region exact LCS deltas vs main (rc.py regions). Experiment only."""
import sys, os, subprocess, json
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import rc, oracle, difflib
OUT = os.path.dirname(T)
RL = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a20-cto-s3flagcolour/llvmb/bin/llc')
LLCA = ['-O3', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext', '-function-sections']
def run(ml, tag, env_extra, asm=False):
    env = dict(os.environ)
    for k, v in env_extra.items():
        env['RAPRIO_' + k] = v
    d = os.path.join(OUT, 'ra'); os.makedirs(d, exist_ok=True)
    log = os.path.join(d, tag + '.log')
    if os.path.exists(log): os.remove(log)
    env['RAPRIO_LOG'] = log
    o = os.path.join(d, tag + '.o')
    r = subprocess.run([RL, *LLCA, ml, '-filetype=obj', '-o', o], env=env, capture_output=True, text=True)
    if r.returncode: return {'tag': tag, 'err': r.stderr[-400:]}
    b = oracle.elf_fn(o, oracle.KEEP); os.remove(o)
    open(os.path.join(d, tag + '.bin'), 'wb').write(b)
    if asm:
        env['RAPRIO_TAG'] = '1'
        subprocess.run([RL, *LLCA, ml, '-filetype=asm', '-o', os.path.join(d, tag + '.s')], env=env, capture_output=True)
    return {'tag': tag, 'bin': os.path.join(d, tag + '.bin')}
if __name__ == '__main__':
    a = sys.argv[1:]; ml, tag = a[0], a[1]; ex = {}; asm = False
    for x in a[2:]:
        if x == '--asm': asm = True; continue
        k, v = x.split('=', 1); ex[k] = v
    res = run(ml, tag, ex, asm)
    if 'err' in res: print(json.dumps(res)); sys.exit(1)
    O = rc.orig_window(); ot, oo = rc.mask(O)
    ref = os.path.join(OUT, 'fx/m0/fn.bin')
    r0, t0, ra0, M0, b0 = rc.per(ref, ot, oo, '')
    d, t, ra, M, b = rc.per(res['bin'], ot, oo, '')
    reg = ' '.join(f'{n}:{d.get(n,0)-r0.get(n,0):+d}' for _, n in rc.REG if d.get(n, 0) != r0.get(n, 0))
    print(json.dumps({'tag': tag, 'M': M, 'dM': M - M0, 'ratio': ra, 'bytes': b, 'lcs': t, 'dlcs': t - t0, 'W2': d.get('W2', 0), 'regions': reg, 'env': ex}))
