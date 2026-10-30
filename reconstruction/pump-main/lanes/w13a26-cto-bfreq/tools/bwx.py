#!/usr/bin/env python3
"""bwx.py: branch-weight / successor-order llc oracle on an extracted admin_cto::execute module (experiment only).
  bwx.py brs <ex.ll>                         list conditional br blocks of execute (label, cond, succs, prof)
  bwx.py run <ex.ll> SPEC                    one run; SPEC = comma list of bw:BLOCK:T:F | inv:BLOCK | strip:BLOCK
  bwx.py sweep <ex.ll> BASESPEC OUT.jsonl [-j N]   every br block x {1:2000, 2000:1} on top of BASESPEC
Scores with exact masked 8-byte tokens (rx.py metric) against the original 0x22a10 window."""
import sys, os, re, json, subprocess, tempfile, struct, difflib, pickle
from concurrent.futures import ThreadPoolExecutor
H = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness'
LLC = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llc')
F = ['-O3', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext', '-function-sections']
KEEP = 'admin_cto7execute'
CACHE = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w13a26-cto-bfreq/orig_toks.pkl')

def mask(raw):
    m = bytearray(raw); i = 0; toks = []
    while i < len(raw):
        op = raw[i]; n = 16 if op == 0x18 else 8
        if op == 0x85: m[i+1] &= 0x0f; m[i+4:i+8] = b'\0'*4
        if op == 0x18: m[i+4:i+8] = b'\0'*4; m[i+12:i+16] = b'\0'*4
        toks.append(bytes(m[i:i+n])); i += n
    return toks

def orig_toks():
    if os.path.exists(CACHE): return pickle.load(open(CACHE, 'rb'))
    sys.path.insert(0, H)
    from score import original_windows
    for w in original_windows():
        if w['start'] == 0x22a10:
            t = mask(w['raw']); pickle.dump(t, open(CACHE, 'wb')); return t

def elf_fn(path, pat=KEEP):
    b = open(path, 'rb').read()
    shoff = struct.unpack_from('<Q', b, 0x28)[0]; shentsize, shnum, shstrndx = struct.unpack_from('<HHH', b, 0x3a)
    sh = [struct.unpack_from('<IIQQQQIIQQ', b, shoff+i*shentsize) for i in range(shnum)]
    for s in sh:
        if s[1] == 2:
            so = sh[s[6]][4]
            for j in range(s[5]//24):
                nm, info, oth, shndx, val, size = struct.unpack_from('<IBBHQQ', b, s[4]+j*24)
                name = b[so+nm:b.index(b'\0', so+nm)].decode()
                if pat in name and (info & 0xf) == 2:
                    sec = sh[shndx]; off = sec[4]+val-(sec[3] if path.endswith('.so') else 0)
                    return b[off:off+size]
    raise SystemExit('fn not found')

def metric(cand, o):
    c = mask(cand)
    r = difflib.SequenceMatcher(None, o, c, autojunk=False).ratio()
    ob = b''.join(o); cb = b''.join(c)
    sd = sum(1 for i in range(0, len(ob), 8) if ob[i:i+8] != cb[i:i+8]) if len(ob) == len(cb) else None
    return round(r, 5), sd, len(cand)

LABEL = re.compile(r'^("(?:[^"\\]|\\.)*"|[-\w.$]+):')
def split(mod):
    m = re.search(r'^define [^\n]*@_ZN14pump_recovered9admin_cto7execute[^\n]*\{\n', mod, re.M)
    i = m.start(); j = mod.index('\n}\n', i) + 3
    return mod[:i], mod[i:j], mod[j:]

def blocks(fn):
    lines = fn.rstrip('\n').split('\n'); head, body, tail = lines[0], lines[1:-1], lines[-1]
    out = [['start', []]]
    for l in body:
        m = LABEL.match(l)
        if m and not l.startswith(' '): out.append([m.group(1).strip('"'), [l]])
        else: out[-1][1].append(l)
    if not out[0][1]: out.pop(0)
    return head, out, tail

BR = re.compile(r'^(\s*)br i1 (%[-\w.$"]+|true|false), label (%[-\w.$]+|%"[^"]+"), label (%[-\w.$]+|%"[^"]+")(.*)$')
def apply(mod, spec):
    pre, fn, post = split(mod); head, bl, tail = blocks(fn); md = []; idx = {b[0]: k for k, b in enumerate(bl)}
    for it in [x for x in spec.split(',') if x]:
        p = it.split(':'); op = p[0]; ls = bl[idx[p[1]]][1]; ti = len(ls)-1
        while not ls[ti].strip() or ls[ti].strip().startswith(';'): ti -= 1
        m = BR.match(ls[ti]); assert m, (it, ls[ti])
        ind, c, a, b, rest = m.groups(); rest = re.sub(r', !prof !\d+', '', rest)
        if op == 'bw':
            n = 9000000+len(md); md.append(f'!{n} = !{{!"branch_weights", i32 {p[2]}, i32 {p[3]}}}')
            ls[ti] = f'{ind}br i1 {c}, label {a}, label {b}{rest}, !prof !{n}'
        elif op == 'strip':
            ls[ti] = f'{ind}br i1 {c}, label {a}, label {b}{rest}'
        elif op == 'inv':
            nm = f'%inv.{len(md)}x{abs(hash(p[1]))%100000}'; md.append('')
            ls[ti:ti+1] = [f'{ind}{nm} = xor i1 {c}, true', f'{ind}br i1 {nm}, label {b}, label {a}{rest}']
    fn = '\n'.join([head]+[l for _, x in bl for l in x]+[tail])+'\n'
    return pre+fn+post+'\n'.join(x for x in md if x)+'\n'

def run(mod, spec, o):
    with tempfile.TemporaryDirectory(dir=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w13a26-cto-bfreq')) as d:
        open(d+'/m.ll', 'w').write(apply(mod, spec))
        r = subprocess.run([LLC, *F, d+'/m.ll', '-filetype=obj', '-o', d+'/m.o'], capture_output=True, text=True)
        if r.returncode: return {'spec': spec, 'error': r.stderr[-300:]}
        rr, sd, nb = metric(elf_fn(d+'/m.o'), o)
        return {'spec': spec, 'ratio': rr, 'slots': sd, 'bytes': nb}

def brs(mod):
    _, fn, _ = split(mod); _, bl, _ = blocks(fn); res = []
    for lab, ls in bl:
        ti = len(ls)-1
        while not ls[ti].strip(): ti -= 1
        m = BR.match(ls[ti])
        if m: res.append((lab, m.group(2), m.group(3), m.group(4), 'prof' in m.group(5)))
    return res

if __name__ == '__main__':
    a = sys.argv[1:]; cmd = a.pop(0); mod = open(a.pop(0)).read()
    if cmd == 'brs':
        for r in brs(mod): print(*r)
    elif cmd == 'run':
        print(json.dumps(run(mod, a[0] if a else '', orig_toks())))
    elif cmd == 'emit':   # emit <ex.ll> SPEC OUT.ll
        open(a[1], 'w').write(apply(mod, a[0]))
    elif cmd == 'sweep':
        base = a.pop(0); outp = a.pop(0); j = int(a[a.index('-j')+1]) if '-j' in a else 6
        o = orig_toks(); items = []; ws = a[a.index('-w')+1].split(',') if '-w' in a else ['1:2000', '2000:1']
        for lab, *_ in brs(mod):
            for w in ws: items.append(f'bw:{lab}:{w}' if w != 'inv' else f'inv:{lab}')
        f = open(outp, 'a')
        def go(it):
            r = run(mod, (base+',' if base else '')+it, o); r['item'] = it
            f.write(json.dumps(r)+'\n'); f.flush(); return r
        with ThreadPoolExecutor(j) as ex: list(ex.map(go, items))
