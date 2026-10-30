#!/usr/bin/env python3
"""iredit.py: composable IR edits of admin_cto::execute for the llc oracle (experiment only).

Spec items (comma-separated; applied in order):
  bw:BLOCK:T:F      branch_weights T:F on the conditional br that ends block BLOCK
  inv:BLOCK         invert that br (xor the condition, swap successors)
  mv:A:B            move alloca %A to just before alloca %B (B=END: after the last alloca)
  nolt:A            drop the lifetime markers of alloca %A (never stack-colored)
  sz:A:N            resize alloca %A to [N x i8]
  blk:A:B           move basic block A to just before block B in the IR layout (B=END: last)
  swapphi:BLOCK     reverse the incoming order of every phi in BLOCK
Block names are the IR labels without '%' (the entry block is 'start').

  iredit.py run <module.ll> <outdir> SPEC         -> one oracle run (ctoracle metrics)
  iredit.py scan <module.ll> <outdir> BASESPEC ITEMS_FILE [-j N]  -> base+item for each line of ITEMS_FILE
  iredit.py brs <module.ll>                       -> list conditional-branch blocks
"""
import json, os, re, subprocess, sys, tempfile, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ctoracle  # noqa: E402

LABEL = re.compile(r'^("(?:[^"\\]|\\.)*"|[-\w.$]+):')


def split_fn(mod):
    sym = ctoracle.SYMRE.search(mod).group(0)
    i, j = ctoracle.fn_bounds(mod, sym)
    return mod[:i], mod[i:j], mod[j:]


def blocks(fn):
    """-> header line, list of [label, lines], closing '}'"""
    lines = fn.rstrip('\n').split('\n')
    head, body, tail = lines[0], lines[1:-1], lines[-1]
    out = [['start', []]]
    for l in body:
        m = LABEL.match(l)
        if m and not l.startswith(' '):
            lab = m.group(1)
            out.append([lab.strip('"'), [l]])
        else:
            out[-1][1].append(l)
    if not out[0][1]:
        out.pop(0)
    elif out[0][1] and LABEL.match(out[0][1][0]) is None:
        pass
    return head, out, tail


def join(head, bl, tail):
    return '\n'.join([head] + [l for _, ls in bl for l in ls] + [tail]) + '\n'


def find_block(bl, name):
    for k, (lab, ls) in enumerate(bl):
        if lab == name:
            return k
    raise KeyError('no block ' + name)


def term_index(ls):
    for k in range(len(ls) - 1, -1, -1):
        s = ls[k].strip()
        if s and not s.startswith(';'):
            return k
    raise ValueError


class Ctx:
    def __init__(self, mod):
        self.pre, fn, self.post = split_fn(mod)
        self.fn = fn
        self.md = []
        self.next_md = 9000000

    def new_md(self, text):
        n = self.next_md; self.next_md += 1
        self.md.append(f'!{n} = {text}')
        return n

    def text(self):
        return self.pre + self.fn + ('\n'.join(self.md) + '\n' if self.md else '') + self.post


def op_bw(c, block, t, f):
    head, bl, tail = blocks(c.fn)
    k = find_block(bl, block); ls = bl[k][1]; ti = term_index(ls)
    s = ls[ti]
    assert s.strip().startswith('br i1'), (block, s)
    s = re.sub(r', !prof !\d+', '', s)
    n = c.new_md(f'!{{!"branch_weights", i32 {int(t)}, i32 {int(f)}}}')
    ls[ti] = s + f', !prof !{n}'
    c.fn = join(head, bl, tail)


def op_inv(c, block):
    head, bl, tail = blocks(c.fn)
    k = find_block(bl, block); ls = bl[k][1]; ti = term_index(ls)
    m = re.match(r'^(\s*)br i1 (%[-\w.$"]+|true|false), label (%[-\w.$"]+|%"[^"]+"), label (%[-\w.$"]+|%"[^"]+")(.*)$', ls[ti])
    assert m, ls[ti]
    ind, cond, a, b, rest = m.groups()
    nm = f'%inv.{abs(hash(block)) % 100000}'
    ls[ti:ti + 1] = [f'{ind}{nm} = xor i1 {cond}, true', f'{ind}br i1 {nm}, label {b}, label {a}{rest}']
    c.fn = join(head, bl, tail)


def op_mv(c, a, b):
    lines = c.fn.split('\n')
    ia = next(k for k, l in enumerate(lines) if re.match(r'\s*%' + re.escape(a) + r' = alloca ', l))
    la = lines.pop(ia)
    if b == 'END':
        ib = max(k for k, l in enumerate(lines) if re.match(r'\s*%\S+ = alloca ', l)) + 1
    else:
        ib = next(k for k, l in enumerate(lines) if re.match(r'\s*%' + re.escape(b) + r' = alloca ', l))
    lines.insert(ib, la)
    c.fn = '\n'.join(lines)


def op_nolt(c, a):
    out, n = re.subn(r'\n\s*call void @llvm\.lifetime\.(?:start|end)\.p0\(i64 \d+, ptr (?:nonnull )?%' + re.escape(a) + r'\)', '', c.fn)
    assert n, 'no lifetime markers for ' + a
    c.fn = out


def op_sz(c, a, n):
    out, k = re.subn(r'(%' + re.escape(a) + r' = alloca )\[\d+ x i8\]', r'\g<1>[' + str(int(n)) + ' x i8]', c.fn)
    assert k == 1, a
    c.fn = out


def op_blk(c, a, b):
    head, bl, tail = blocks(c.fn)
    k = find_block(bl, a); item = bl.pop(k)
    if b == 'END':
        bl.append(item)
    else:
        bl.insert(find_block(bl, b), item)
    c.fn = join(head, bl, tail)


def op_swapphi(c, block):
    head, bl, tail = blocks(c.fn)
    k = find_block(bl, block); ls = bl[k][1]
    for i, l in enumerate(ls):
        m = re.match(r'^(\s*%[-\w.$"]+ = phi [^\[]+)(\[.*\])(.*)$', l)
        if m:
            parts = re.findall(r'\[[^\[\]]*\]', m.group(2))
            ls[i] = m.group(1) + ', '.join(reversed(parts)) + m.group(3)
    c.fn = join(head, bl, tail)


OPS = dict(bw=op_bw, inv=op_inv, mv=op_mv, nolt=op_nolt, sz=op_sz, blk=op_blk, swapphi=op_swapphi)


def split_spec(spec):
    """items are comma-separated; a label containing commas must be quoted with {}"""
    out, cur, depth = [], '', 0
    for ch in spec:
        if ch == '{': depth += 1; continue
        if ch == '}': depth -= 1; continue
        if ch == ',' and depth == 0:
            out.append(cur); cur = ''
        else:
            cur += ch
    if cur: out.append(cur)
    return [x for x in out if x.strip()]


def apply(mod, spec):
    c = Ctx(mod)
    for item in split_spec(spec):
        parts = item.split(':')
        OPS[parts[0]](c, *parts[1:])
    return c.text()


def run_spec(module_text, outdir, spec, keep=False):
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    t = apply(module_text, spec) if spec else module_text
    p = outdir / 'm.ll'; p.write_text(t)
    r = subprocess.run(ctoracle.LLC + [str(p), '-filetype=obj', '-o', str(outdir / 'm.o')], capture_output=True, text=True)
    if r.returncode:
        if not keep: p.unlink()
        return {'error': r.stderr[-600:]}
    sym = ctoracle.SYMRE.search(module_text).group(0)
    ctok, raw, _ = ctoracle.obj_tokens(outdir / 'm.o', sym)
    otok, w = ORIG
    m = ctoracle.metrics(otok, ctok, len(raw), w['bytes'])
    if os.environ.get('PF'):
        import framebound
        m['pf_ratio'] = framebound.bound(ctok)[1]
    (outdir / 'fn.bin').write_bytes(b''.join(ctok))
    if not keep:
        p.unlink(); (outdir / 'm.o').unlink()
    return m


ORIG = None


def main():
    global ORIG
    ORIG = ctoracle.orig_tokens()
    cmd = sys.argv[1]
    if cmd == 'brs':
        mod = Path(sys.argv[2]).read_text()
        _, fn, _ = split_fn(mod); head, bl, tail = blocks(fn)
        for lab, ls in bl:
            s = ls[term_index(ls)].strip()
            if s.startswith('br i1'):
                print(lab)
        return
    mod = Path(sys.argv[2]).read_text(); out = Path(sys.argv[3])
    if cmd == 'run':
        spec = sys.argv[4] if len(sys.argv) > 4 else ''
        print(json.dumps(run_spec(mod, out, spec, keep=True)))
        return
    base = sys.argv[4]; items = [l.strip() for l in open(sys.argv[5]) if l.strip()]
    j = int(sys.argv[sys.argv.index('-j') + 1]) if '-j' in sys.argv else 6
    res = {}
    def one(k_item):
        k, item = k_item
        spec = ','.join(x for x in (base, item) if x)
        try:
            m = run_spec(mod, out / f'w{threading.get_ident()}', spec)
        except Exception as e:  # noqa
            m = {'error': repr(e)[:300]}
        return item, m
    with ThreadPoolExecutor(j) as ex:
        for item, m in ex.map(one, list(enumerate(items))):
            res[item] = m
            print(json.dumps({'item': item, **m}), flush=True)
    (out / 'scan.json').write_text(json.dumps(res, indent=0))


if __name__ == '__main__':
    main()
