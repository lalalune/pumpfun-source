#!/usr/bin/env python3
"""irre.py <m.ll> <outjsonl> [--only NAME,...] [--jobs N] [--mode reload|sink]: re-read oracle (experiment only).

For every `load` in admin_cto::execute whose value is used in another block, make a variant where each other
block that uses it gets its own fresh load of the same pointer right before its first use (source analogue:
read the field again at the use site instead of holding a local). llc + score (target_metric tokens).
"""
import sys, os, re, subprocess, json, struct, difflib, concurrent.futures as cf, tempfile
H = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness'
SDK = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
KEEP = 'admin_cto7execute'


def elf_fn(path, pat=KEEP):
    b = open(path, 'rb').read()
    shoff = struct.unpack_from('<Q', b, 0x28)[0]; shentsize, shnum, shstrndx = struct.unpack_from('<HHH', b, 0x3a)
    sh = [struct.unpack_from('<IIQQQQIIQQ', b, shoff + i * shentsize) for i in range(shnum)]
    for i, s in enumerate(sh):
        if s[1] == 2:
            so = sh[s[6]][4]
            for j in range(s[5] // 24):
                nm, info, oth, shndx, val, size = struct.unpack_from('<IBBHQQ', b, s[4] + j * 24)
                name = b[so + nm:b.index(b'\0', so + nm)].decode()
                if pat in name and (info & 0xf) == 2:
                    sec = sh[shndx]; off = sec[4] + val - (sec[3] if path.endswith('.so') else 0)
                    return b[off:off + size]


def mask(raw):
    m = bytearray(raw); i = 0; toks = []
    while i < len(raw):
        op = raw[i]; n = 16 if op == 0x18 else 8
        if op == 0x85: m[i + 1] &= 0x0f; m[i + 4:i + 8] = b'\0' * 4
        if op == 0x18: m[i + 4:i + 8] = b'\0' * 4; m[i + 12:i + 16] = b'\0' * 4
        toks.append(bytes(m[i:i + n])); i += n
    return toks


def orig():
    sys.path.insert(0, H)
    from score import original_windows
    for w in original_windows():
        if w['start'] == 0x22a10: return mask(w['raw'])


TOK = r'(?![\w.$])'


def split_fn(text):
    i = text.index('\ndefine ', text.index('admin_cto7execute') - 400) if False else None
    m = re.search(r'^define [^\n]*admin_cto7execute[^\n]*\{$', text, re.M)
    a = m.start(); b = text.index('\n}\n', a) + 3
    return text[:a], text[a:b], text[b:]


def parse(fn):
    L = fn.split('\n'); blk = []; cur = 'entry'
    for l in L:
        m = re.match(r'^([\w.$"-]+):', l)
        if m: cur = m.group(1)
        blk.append(cur)
    return L, blk


def variants(fn, only=None):
    L, blk = parse(fn)
    out = []
    for i, l in enumerate(L):
        m = re.match(r'^\s+(%[\w.$]+) = load (\S+), ptr (%[\w.$]+|@[\w.$]+)(.*)$', l)
        if not m: continue
        v, ty, p, rest = m.groups()
        if only and v not in only: continue
        rx = re.compile(re.escape(v) + TOK)
        uses = {}
        for k, u in enumerate(L):
            if k == i or not rx.search(u) or ' = phi ' in u: continue
            if blk[k] != blk[i]: uses.setdefault(blk[k], []).append(k)
        if not uses: continue
        out.append((v, ty, p, rest, i, uses))
        if SUB and len(uses) > 1:
            for b in uses: out.append((v + '@' + b, ty, p, rest, i, {b: uses[b]}))
    return L, out


SUB = '--sub' in sys.argv
def make(L, var, tag='rl'):
    v, ty, p, rest, i, uses = var; v = v.split('@')[0]
    N = list(L); ins = {}
    for n, (b, ks) in enumerate(uses.items()):
        nv = '%s.%s%d' % (v, tag, n); rx = re.compile(re.escape(v) + TOK)
        for k in ks: N[k] = rx.sub(nv, N[k])
        ins[ks[0]] = '  %s = load %s, ptr %s%s' % (nv, ty, p, rest)
    R = []
    for k, l in enumerate(N):
        if k in ins: R.append(ins[k])
        R.append(l)
    return '\n'.join(R)


def run(pre, fn, post, O, d):
    os.makedirs(d, exist_ok=True)
    open(d + '/m.ll', 'w').write(pre + fn + post)
    r = subprocess.run([SDK + '/llc', '-O3', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext', '-function-sections', d + '/m.ll', '-filetype=obj', '-o', d + '/m.o'], capture_output=True, text=True)
    if r.returncode: return {'error': r.stderr[-300:]}
    c = mask(elf_fn(d + '/m.o'))
    rr = difflib.SequenceMatcher(None, O, c, autojunk=False).ratio()
    nb = sum(len(t) for t in c)
    res = {'ratio': round(rr, 5), 'bytes': nb}
    if nb == sum(len(t) for t in O):
        res['slots'] = sum(1 for a, b in zip(b''.join(O)[0::8], b''.join(c)[0::8]) if a != b)
        ob = b''.join(O); cb = b''.join(c); res['slots'] = sum(1 for q in range(0, nb, 8) if ob[q:q + 8] != cb[q:q + 8])
    return res


def main():
    a = sys.argv[1:]; m = a.pop(0); outp = a.pop(0); only = None; jobs = 6
    while a:
        x = a.pop(0)
        if x == '--only': only = set(a.pop(0).split(','))
        elif x == '--jobs': jobs = int(a.pop(0))
        elif x == '--sub': pass
    text = open(m).read(); pre, fn, post = split_fn(text); O = orig()
    L, vs = variants(fn, only)
    base = run(pre, fn, post, O, tempfile.mkdtemp(prefix='irre'))
    print('base', base, 'candidates', len(vs), flush=True)
    work = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a03-cto-liverange/var/irre')
    def job(var):
        d = work + '/' + re.sub(r'[^\w]', '_', var[0])
        r = run(pre, make(L, var), post, O, d)
        r.update({'v': var[0], 'ptr': var[2], 'blocks': len(var[5]), 'line': L[var[4]].strip()[:120]})
        for f in ('m.ll', 'm.o'):
            try: os.remove(d + '/' + f)
            except OSError: pass
        return r
    with open(outp, 'w') as f, cf.ThreadPoolExecutor(jobs) as ex:
        for r in ex.map(job, vs):
            r['d'] = round(r.get('ratio', 0) - base['ratio'], 5) if 'ratio' in r else None
            f.write(json.dumps(r) + '\n'); f.flush()
            if r.get('d') and r['d'] > 0: print('GAIN', r, flush=True)


main()
