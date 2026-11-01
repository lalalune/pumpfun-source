#!/usr/bin/env python3
"""ordor.py: exact spill-colour ORDER oracle (experiment only).
evalorder(mll, order) runs the private llc (w15a32 SSC_WSET hook, w16a20 build) with EVERY interval's weight set
explicitly (strictly decreasing along `order`), so the colouring processes intervals in exactly that order.
Code is untouched; the result is the binary that this code would give with that colour order (incl. tail merging).
"""
import os, sys, subprocess, tempfile, hashlib
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import sscsim
oracle = sscsim.oracle
PL = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a20-cto-s3flagcolour/llvmb/bin/llc')
LLCA = ['-O3', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext', '-function-sections']
O = None

def spec_of(order):
    n = len(order)
    return ','.join(f'{s}:={(n - i) * 1.0:.1f}' for i, s in enumerate(order))

def llc(mll, env_extra=None, extra=()):
    fd, p = tempfile.mkstemp(suffix='.o'); os.close(fd)
    env = dict(os.environ); env.pop('SSC_WSET', None)
    if env_extra: env.update(env_extra)
    r = subprocess.run([PL, *LLCA, mll, '-filetype=obj', '-o', p, *extra], capture_output=True, text=True, env=env)
    if r.returncode: os.remove(p); raise RuntimeError(r.stderr[-400:])
    b = oracle.elf_fn(p, oracle.KEEP); os.remove(p); return b

def M(b):
    global O
    import difflib
    if O is None: O = oracle.mask(oracle.orig_window())
    c = oracle.mask(b); sm = difflib.SequenceMatcher(None, O, c, autojunk=False)
    m = sum(x.size for x in sm.get_matching_blocks()); return m, round(2 * m / (len(O) + len(c)), 5)

def evalorder(mll, order):
    b = llc(mll, {'SSC_WSET': spec_of(order)})
    m, r = M(b)
    return {'M': m, 'ratio': r, 'bytes': len(b), 'sig': hashlib.sha1(b).hexdigest()[:10]}

def evalspec(mll, spec):
    b = llc(mll, {'SSC_WSET': spec} if spec else None)
    m, r = M(b)
    return {'M': m, 'ratio': r, 'bytes': len(b), 'sig': hashlib.sha1(b).hexdigest()[:10]}

if __name__ == '__main__':
    mll, d = sys.argv[1], sys.argv[2]
    S = sscsim.Sim(d)
    print('natural', evalspec(mll, ''))
    print('base order full spec', evalorder(mll, S.order))
