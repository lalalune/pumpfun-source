#!/usr/bin/env python3
"""frameoracle.py: predict and explain the r10 stack-frame layout of one function.

From rustc's LLVM IR (whole module, as captured with --emit=llvm-ir), run the SDK llc
exactly like fastbuild and dump the frame at three points:
  before stack-coloring (every alloca-backed frame object, with its IR name),
  after stack-coloring (which objects were merged into which slot),
  after prologepilog (final [SP-T] location of every surviving object).
Then align the candidate's instruction stream against the ORIGINAL window with all r10
offsets abstracted, and for each surviving candidate object compute the implied original
location (votes over aligned stack accesses).  The output is the frame in layout order:

  fi  T(cand)  T(orig-implied)  delta  size  lifetime  merged-objects (IR names)

The layout rule (verified on every target: --check prints mismatches) is plain PEI:
objects are placed in frame-index order, T = alignup(T_prev + size, align), and frame-index
order is alloca order (inlined callee allocas first, then the function's own allocas in
reverse MIR-local order). StackColoring merges a slot into an earlier-sorted (larger) slot
only when both have lifetime markers; an alloca with no LIFETIME_START is never merged.

A change of delta between two consecutive surviving objects is therefore exactly the
number of bytes the original has more (positive) or fewer (negative) between them: the
most actionable statement about what source change is needed.  `--breaks` lists them.

Usage:
  frameoracle.py --ir module.ll --sym REGEX --win 0xADDR [--edit edit.py] [--name N]
                 [--out DIR] [--so unstripped.so] [--what-if 'ins:FI:SIZE,del:FI,size:FI:SIZE']
edit.py defines edit(fn_text)->fn_text applied to the function's IR definition.
--so: also check that llc reproduces the fastbuild function bytes (normalized).
"""
import argparse, collections, difflib, os, re, runpy, struct, subprocess, sys, json
from pathlib import Path

HERE = Path(__file__).resolve()
HARN = HERE.parents[3] / 'harness'
SDK = Path.home() / '.cache/solana/v1.44/platform-tools/llvm/bin'
sys.path.insert(0, str(HARN))


def load_score():
    av = sys.argv; sys.argv = av[:1]
    import score
    sys.argv = av
    return score


# ---------------------------------------------------------------- sBPF decoding
def decode(raw):
    """-> list of dict(i, op, dst, src, off, imm, size)"""
    out = []; i = 0
    while i < len(raw):
        op, regs, off, imm = struct.unpack_from('<BBhi', raw, i)
        k = 16 if op == 0x18 else 8
        out.append(dict(i=i, op=op, dst=regs & 15, src=regs >> 4, off=off, imm=imm, k=k))
        i += k
    return out


def stack_off(x):
    """positive r10 displacement (T - inner) of a load/store, else None"""
    cls = x['op'] & 7
    if cls == 1 and x['src'] == 10 and x['op'] != 0x18:  # LDX
        return -x['off']
    if cls in (2, 3) and x['dst'] == 10:  # ST / STX
        return -x['off']
    return None


def tokens(ins):
    """abstract tokens + stack offsets (per insn: list of positive r10 displacements)"""
    toks = []; offs = []
    for j, x in enumerate(ins):
        op = x['op']; so = stack_off(x); o = []
        if so is not None:
            t = (op, x['dst'], x['src'], 'S'); o = [so]
            if (op & 7) == 2: t = t + (x['imm'],)
        elif op == 0x07 and j > 0 and ins[j - 1]['op'] == 0xbf and ins[j - 1]['src'] == 10 \
                and ins[j - 1]['dst'] == x['dst']:
            t = (op, x['dst'], 'A'); o = [-x['imm']]
        elif op == 0x85:
            t = (op, x['src'])
        elif op == 0x18:
            t = (op, x['dst'])
        elif (op & 7) == 5 and op not in (0x85, 0x95):
            t = (op, x['dst'], x['src'], x['imm'] if op & 8 == 0 else 'r')
        else:
            t = (op, x['dst'], x['src'], x['off'], x['imm'])
        toks.append(t); offs.append(o)
    return toks, offs


# ---------------------------------------------------------------- MIR frame dumps
FI = re.compile(r'^\s*fi#(-?\d+): (?:(dead)|size=(\d+), align=(\d+)(, fixed)?(?:, (?!at )[\w-]+)*(?:, at location \[SP([+-]\d+)?\])?)')


def split_dumps(text):
    parts = re.split(r'^# \*\*\* IR Dump (Before|After) .*?\((\S+)\) \*\*\*:\s*$', text, flags=re.M)
    d = {}
    for k in range(1, len(parts), 3):
        d[(parts[k], parts[k + 1])] = parts[k + 2]
    return d


def frame_objects(dump):
    objs = {}
    for l in dump.splitlines():
        m = FI.match(l)
        if not m: continue
        fi = int(m.group(1))
        if m.group(2):
            objs[fi] = dict(fi=fi, dead=True); continue
        objs[fi] = dict(fi=fi, dead=False, size=int(m.group(3)), align=int(m.group(4)),
                        fixed=bool(m.group(5)),
                        # MachineFrameInfo::print omits the location when SPOffset == -1
                        loc=int(m.group(6) or 0) if 'location' in l else -1)
    return objs


SREF = re.compile(r'%stack\.(\d+)(?:\.([^\s,:)]+))?')


def body_lines(dump):
    i = dump.find('\n0B\t'); i = dump.find('bb.0') if i < 0 else i
    return [l for l in dump[i:].splitlines() if l.strip() and not l.startswith('#')]


def short_sym(sym):
    """_ZN..E -> last two path components (cheap demangle)"""
    sym = sym.strip('"')
    if not sym.startswith('_ZN'): return sym
    i = 3; parts = []
    while i < len(sym) and sym[i].isdigit():
        j = i
        while sym[j].isdigit(): j += 1
        n = int(sym[i:j]); parts.append(sym[j:j + n]); i = j + n
    parts = [x for x in parts if not re.fullmatch(r'h[0-9a-f]{16}', x)]
    out = '::'.join(parts[-2:])
    for k, v in (('$LT$', '<'), ('$GT$', '>'), ('$u20$', ' '), ('$u7b$', '{'), ('$u7d$', '}'), ('$C$', ','), ('..', '::')):
        out = out.replace(k, v)
    return out


def names_and_marks(dump):
    """IR names of alloca-backed objects, LIFETIME_START counts, and labels for ISel temporaries:
    an unnamed object first used as `MOV_rr %stack.N` right before a call is the hidden return
    slot of a call returning a 16-byte value ({i64, ptr}); label it ret:<callee>."""
    names = {}; lt = collections.Counter(); L = body_lines(dump); first = {}
    for k, l in enumerate(L):
        for m in SREF.finditer(l):
            fi = int(m.group(1))
            if m.group(2): names.setdefault(fi, m.group(2))
            else: first.setdefault(fi, k)
            if 'LIFETIME_START' in l: lt[fi] += 1
    for fi, k in first.items():
        if fi in names: continue
        for l in L[k:k + 24]:
            m = re.search(r'JAL @(\S+?),', l) or re.search(r'JAL @(\S+)$', l)
            if m: names[fi] = 'ret:' + short_sym(m.group(1)); break
    return names, lt


def merge_map(before, after):
    """align instruction lines (LIFETIME_* dropped, stack refs abstracted) -> fi_before -> fi_after"""
    def prep(dump):
        L = []
        for l in body_lines(dump):
            if 'LIFETIME_' in l: continue
            refs = [int(m.group(1)) for m in SREF.finditer(l)]
            key = SREF.sub('%stack', re.sub(r'^\s*\d+B\s*', '', l)).strip()
            L.append((key, refs))
        return L
    a = prep(before); b = prep(after)
    sm = difflib.SequenceMatcher(None, [x[0] for x in a], [x[0] for x in b], autojunk=False)
    mp = collections.defaultdict(collections.Counter)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'equal': continue
        for k in range(i2 - i1):
            for x, y in zip(a[i1 + k][1], b[j1 + k][1]): mp[x][y] += 1
    return {x: c.most_common(1)[0][0] for x, c in mp.items()}


# ---------------------------------------------------------------- llc
def ir_move_alloca(fn, a, b):
    lines = fn.split('\n')
    ia = next(k for k, l in enumerate(lines) if re.match(r'\s*%' + re.escape(a) + r' = alloca ', l))
    la = lines.pop(ia)
    if b == 'END':
        ib = max(k for k, l in enumerate(lines) if re.match(r'\s*%\S+ = alloca ', l)) + 1
    else:
        ib = next(k for k, l in enumerate(lines) if re.match(r'\s*%' + re.escape(b) + r' = alloca ', l))
    lines.insert(ib, la)
    return '\n'.join(lines)


def ir_drop_lifetime(fn, a):
    out, n = re.subn(r'\n\s*call void @llvm\.lifetime\.(?:start|end)\.p0\(i64 \d+, ptr (?:nonnull )?%' + re.escape(a) + r'\)', '', fn)
    assert n, 'no lifetime markers for ' + a
    return out


def mir_locals(path, rx):
    t = Path(path).read_text()
    m = re.search(rx, t, flags=re.M)
    if not m: return {}
    body = t[m.start(): t.index('\n}\n', m.start())]
    ty = {}
    for x in re.finditer(r'^\s*let (?:mut )?(_\d+): ([^;]+);', body, flags=re.M): ty[x.group(1)] = x.group(2)
    for x in re.finditer(r'^\s*debug (\S+) => (_\d+);', body, flags=re.M):
        ty[x.group(2)] = ty.get(x.group(2), '') + '  [' + x.group(1) + ']'
    return ty


def run_llc(mod_path, sym, d, extra=()):
    o = d / 'm.o'
    cmd = [str(SDK / 'llc'), '-O3', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext', str(mod_path),
           '-filetype=obj', '-o', str(o), '-print-before=stack-coloring', '-print-after=stack-coloring',
           '-print-after=prologepilog', '-filter-print-funcs=' + sym] + list(extra)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit('llc failed:\n' + r.stderr[-3000:])
    (d / 'mir.txt').write_text(r.stderr)
    # function bytes
    t = subprocess.check_output([str(SDK / 'llvm-readelf'), '-sSW', str(o)], text=True)
    secs = {}
    for l in t.splitlines():
        m = re.match(r'\s*\[\s*(\d+)\]\s+(\S+)\s+\S+\s+[0-9a-f]+\s+([0-9a-f]+)\s+([0-9a-f]+)', l)
        if m: secs[int(m.group(1))] = (m.group(2), int(m.group(3), 16))
    blob = o.read_bytes()
    for l in t.splitlines():
        f = l.split()
        if len(f) >= 8 and f[-1] == sym and f[3] == 'FUNC':
            val, size, ndx = int(f[1], 16), int(f[2]), int(f[6])
            off = secs[ndx][1]
            return r.stderr, blob[off + val: off + val + size]
    sys.exit('symbol not found in object')


def norm_calls(raw):
    b = bytearray(raw)
    for x in decode(raw):
        if x['op'] == 0x85 and x['src'] == 1: b[x['i'] + 4:x['i'] + 8] = bytes(4)
        if x['op'] == 0x18: b[x['i'] + 4:x['i'] + 8] = bytes(4); b[x['i'] + 12:x['i'] + 16] = bytes(4)
    return bytes(b)


# ---------------------------------------------------------------- analysis
def layout(objs):
    """re-simulate PEI: sequential placement in fi order"""
    T = 0; res = {}
    for fi in sorted(o for o in objs if o >= 0):
        x = objs[fi]
        if x['dead']: continue
        T = T + x['size']; a = x['align']; T = (T + a - 1) // a * a
        res[fi] = T
    return res


def analyze(orig_raw, cand_raw, final, names, lt, mm, out, args):
    oi = decode(orig_raw); ci = decode(cand_raw)
    ot, oo = tokens(oi); ct, co = tokens(ci)
    sm = difflib.SequenceMatcher(None, ot, ct, autojunk=False)
    live = {fi: x for fi, x in final.items() if fi >= 0 and not x['dead']}
    spans = sorted(((-x['loc'], x['size'], fi) for fi, x in live.items()))

    def obj_of(c):
        for T, s, fi in spans:
            if T - s < c <= T: return fi, T
        return None
    votes = collections.defaultdict(collections.Counter)
    pairs = 0; eqoff = 0
    covered_orig = collections.Counter()
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'equal': continue
        for k in range(i2 - i1):
            for a, c in zip(oo[i1 + k], co[j1 + k]):
                pairs += 1; eqoff += a == c
                ob = obj_of(c)
                if ob:
                    fi, T = ob; votes[fi][a + (T - c)] += 1; covered_orig[a] += 1
    merged_into = collections.defaultdict(list)
    for x, y in mm.items(): merged_into[y].append(x)
    rows = []
    for T, s, fi in sorted(spans):
        v = votes.get(fi, collections.Counter()); tot = sum(v.values())
        best = v.most_common(1)[0] if v else (None, 0)
        members = sorted(set(merged_into.get(fi, [])) | {fi})
        rows.append(dict(fi=fi, T=T, size=s, align=live[fi]['align'], orig=best[0], votes=best[1], tot=tot,
                         delta=(best[0] - T) if best[0] is not None else None,
                         lt=lt.get(fi, 0), name=names.get(fi, ''),
                         members=[(m, names.get(m, ''), lt.get(m, 0)) for m in members if m != fi],
                         alt=[(k - T, n) for k, n in v.most_common(3)[1:]]))
    # original-side stack offsets not explained by any aligned candidate access
    allo = collections.Counter(a for o in oo for a in o)
    return dict(ratio=sm.ratio(), pairs=pairs, offeq=eqoff, rows=rows,
                orig_offsets=allo, covered=covered_orig,
                frame_orig=max(allo) if allo else 0,
                frame_cand=max((a for o in co for a in o), default=0))


def confident(r, minv):
    return r['delta'] is not None and r['votes'] >= minv and r['votes'] * 2 > r['tot']


def breaks(rows, minv=2):
    """consecutive confident objects whose delta changes: bytes the original has more/less between them"""
    out = []; prev = None
    for r in rows:
        if not confident(r, minv): continue
        if prev is not None and r['delta'] != prev['delta']:
            out.append((prev, r, r['delta'] - prev['delta']))
        prev = r
    return out


def what_if(final, spec):
    """apply edits to the surviving-object list and re-layout. spec: ins:FI:SIZE[:ALIGN] (new object
    just before FI), del:FI, size:FI:SIZE"""
    objs = {k: dict(v) for k, v in final.items() if k >= 0}
    order = [k for k in sorted(objs) if not objs[k]['dead']]
    seq = [(k, objs[k]['size'], objs[k]['align']) for k in order]
    for e in spec.split(','):
        p = e.split(':')
        if p[0] == 'del': seq = [x for x in seq if x[0] != int(p[1])]
        elif p[0] == 'size': seq = [(k, int(p[2]) if k == int(p[1]) else s, a) for k, s, a in seq]
        elif p[0] == 'ins':
            j = next(i for i, x in enumerate(seq) if x[0] == int(p[1]))
            seq.insert(j, (f'new{len(seq)}', int(p[2]), int(p[3]) if len(p) > 3 else 8))
    T = 0; res = {}
    for k, s, a in seq:
        T = T + s; T = (T + a - 1) // a * a; res[k] = T
    return res


def partition(a, mod_path, sym, d, orig, mm, final, names, lt, rep, P):
    """-no-stack-coloring run: every alloca keeps its own slot, so aligned accesses give each
    alloca's implied ORIGINAL slot.  Allocas sharing an implied orig T form the original's
    StackColoring groups; compare them with ours."""
    dn = d / 'nosc'; dn.mkdir(exist_ok=True)
    text, cand = run_llc(mod_path, sym, dn, list(a.llc) + ['-no-stack-coloring'])
    dumps = split_dumps(text)
    fin = frame_objects(dumps[('After', 'prologepilog')])
    r2 = analyze(orig, cand, fin, names, lt, {}, dn, a)
    imp = {r['fi']: r for r in r2['rows'] if r['fi'] in names or True}
    ours_rep = {}
    for x in fin:
        if x < 0 or fin[x]['dead']: continue
        ours_rep[x] = mm.get(x, x)
    # original groups: allocas with confident implied T
    og = collections.defaultdict(list)
    for fi, r in imp.items():
        if confident(r, a.minv): og[r['orig']].append(fi)
    P('\n# ORIGINAL StackColoring groups (per-alloca implied orig T from the -no-stack-coloring run)')
    P('#   T_orig  members (ours: slot fi->T) ; "!" = alloca sits in a different group in ours; "*" = no lifetime marker in ours')
    ours_T = {fi: -final[fi]['loc'] for fi in final if fi >= 0 and not final[fi]['dead']}
    mism = 0
    for T in sorted(og):
        mem = sorted(og[T])
        slots = collections.Counter(ours_rep.get(f, f) for f in mem)
        main_slot = slots.most_common(1)[0][0]
        parts = []
        for f in mem:
            sl = ours_rep.get(f, f); bad = sl != main_slot
            mism += bad
            parts.append(f'{names.get(f, "") or "#"}#{f}/{imp[f]["size"]}{"*" if not lt.get(f) else ""}{"!" if bad else ""}')
        P(f'  {T:#6x}  ours slot fi{main_slot}@{ours_T.get(main_slot, 0):#x}: ' + ' '.join(parts))
    # ours groups split in orig
    P('\n# OUR groups whose members the original places in different slots')
    grp = collections.defaultdict(list)
    for f, sl in ours_rep.items(): grp[sl].append(f)
    for sl in sorted(grp):
        Ts = collections.defaultdict(list)
        for f in grp[sl]:
            r = imp.get(f)
            if r and confident(r, a.minv): Ts[r['orig']].append(f)
        if len(Ts) > 1:
            P(f'  ours fi{sl}@{ours_T.get(sl, 0):#x}: ' + ' | '.join(
                f'orig {T:#x}: ' + ','.join(f'{names.get(f, "") or "#"}#{f}' for f in fs) for T, fs in sorted(Ts.items())))
    # alloca order: rep of each orig group (largest member, lowest fi = StackColoring's choice)
    reps = []
    for T in sorted(og):
        mem = og[T]; big = max(imp[f]['size'] for f in mem)
        reps.append((T, min(f for f in mem if imp[f]['size'] == big)))
    seq = [f for T, f in reps]
    # longest increasing subsequence of our fi numbers along the original layout
    import bisect
    tails = []; idx = []; prev = [-1] * len(seq)
    for i, v in enumerate(seq):
        k = bisect.bisect_left(tails, v)
        if k == len(tails): tails.append(v); idx.append(i)
        else: tails[k] = v; idx[k] = i
        prev[i] = idx[k - 1] if k else -1
    keep = set(); i = idx[-1] if idx else -1
    while i >= 0: keep.add(i); i = prev[i]
    P('\n# ALLOCA ORDER: original slot reps in orig-T order; out-of-order ones (not in the LIS of our fi) need a different alloca position')
    for i, (T, f) in enumerate(reps):
        if i in keep: continue
        before = next((reps[j][1] for j in range(i - 1, -1, -1) if j in keep), None)
        after = next((reps[j][1] for j in range(i + 1, len(reps)) if j in keep), None)
        P(f'  {names.get(f, "") or "#"}#{f}/{imp[f]["size"]} at orig {T:#x}: orig puts it between fi{before} '
          f'{names.get(before, "")} and fi{after} {names.get(after, "")}')
    unk = [f for f in imp if not confident(imp[f], a.minv) and f in names]
    P(f'\n# allocas without a confident orig slot: {len(unk)}: ' + ' '.join(f'{names[f]}#{f}' for f in sorted(unk)))
    P(f'# group mismatches: {mism}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--ir', required=True); ap.add_argument('--sym', required=True)
    ap.add_argument('--win', required=True); ap.add_argument('--edit'); ap.add_argument('--name', default='base')
    ap.add_argument('--out', default=str(Path.home() / '.cache/pumpfun-reconstruction/lanes/w4-frame-oracle/fo'))
    ap.add_argument('--so'); ap.add_argument('--what-if'); ap.add_argument('--minv', type=int, default=2)
    ap.add_argument('--json'); ap.add_argument('--llc', nargs='*', default=[])
    ap.add_argument('--quiet', action='store_true')
    ap.add_argument('--move-alloca', action='append', default=[], metavar='A:B',
                    help='IR what-if: move alloca %%A to just before alloca %%B (B="END": after the last alloca)')
    ap.add_argument('--drop-lifetime', action='append', default=[], metavar='A',
                    help='IR what-if: delete llvm.lifetime.start/end of alloca %%A (it then never merges)')
    ap.add_argument('--mir', help='rustc --emit=mir output: annotate _N allocas with their MIR type / debug name')
    ap.add_argument('--mir-fn', action='append', default=[], help='regex selecting the function header line in --mir (e.g. "^fn swap_hop\\(")')
    ap.add_argument('--no-partition', action='store_true', help='skip the -no-stack-coloring per-alloca run')
    a = ap.parse_args()
    d = Path(a.out) / a.name; d.mkdir(parents=True, exist_ok=True)
    mod = Path(a.ir).read_text()
    m = re.search(r'^define [^\n]*@(' + a.sym + r')\(', mod, flags=re.M)
    if not m: sys.exit('no function matching ' + a.sym)
    sym = m.group(1)
    mod_path = Path(a.ir)
    if a.edit or a.move_alloca or a.drop_lifetime:
        i = m.start(); j = mod.index('\n}\n', i) + 3
        fn = mod[i:j]; fn2 = runpy.run_path(a.edit)['edit'](fn) if a.edit else fn
        for mv in a.move_alloca: fn2 = ir_move_alloca(fn2, *mv.split(':'))
        for nm in a.drop_lifetime: fn2 = ir_drop_lifetime(fn2, nm)
        assert fn2 != fn, 'edit changed nothing'
        mod_path = d / 'm.ll'; mod_path.write_text(mod[:i] + fn2 + mod[j:])
    text, cand = run_llc(mod_path, sym, d, a.llc)
    (d / 'fn.bin').write_bytes(cand)
    dumps = split_dumps(text)
    before = dumps[('Before', 'stack-coloring')]; after = dumps[('After', 'stack-coloring')]
    pei = dumps[('After', 'prologepilog')]
    names, lt = names_and_marks(before)
    if a.mir and a.mir_fn:
        # first --mir-fn: the function itself; second (optional): the LLVM-inlined callee whose
        # locals carry one '.i' suffix (e.g. a closure); deeper inlines are left unannotated
        tys = [mir_locals(a.mir, rx) for rx in a.mir_fn]
        for fi, nm in list(names.items()):
            parts = nm.split('.'); base = parts[0]
            depth = sum(1 for x in parts[1:] if re.fullmatch(r'i\d*', x))
            if depth < len(tys) and base in tys[depth] and (depth == 0 or re.fullmatch(r'i\d*', parts[-1])):
                names[fi] = nm + '{' + re.sub(r'\s+', '', tys[depth][base])[:56] + '}'
    mm = merge_map(before, after)
    final = frame_objects(pei)
    pre = frame_objects(before)
    sc = load_score()
    W = {x['start']: x for x in sc.original_windows()}
    orig = W[int(a.win, 16)]['raw']
    rep = analyze(orig, cand, final, names, lt, mm, d, a)
    sim = layout(final)
    bad = [fi for fi, T in sim.items() if -final[fi]['loc'] != T]
    P = print if not a.quiet else (lambda *x, **k: None)
    def mtok(raw):
        return [norm_calls(raw[x['i']:x['i'] + x['k']]) for x in decode(raw)]
    exact = difflib.SequenceMatcher(None, mtok(orig), mtok(cand), autojunk=False).ratio()
    P(f'# {sym}  window {a.win}  masked-exact-ratio {exact:.5f} (calls/lddw imm masked; ~target_metric ratio)')
    P(f'cand bytes {len(cand)} orig {len(orig)}  abstracted-ratio {rep["ratio"]:.4f}  '
      f'r10 pairs {rep["pairs"]} equal {rep["offeq"]}  max-off cand {rep["frame_cand"]:#x} orig {rep["frame_orig"]:#x}')
    P(f'objects: allocas {sum(1 for f in pre if f >= 0)}  surviving {len(rep["rows"])}  '
      f'merged {sum(1 for x, y in mm.items() if x != y)}  no-lifetime {sum(1 for f in pre if f >= 0 and not lt.get(f) and not pre[f]["dead"])}  '
      f'PEI rule check: {"ok" if not bad else "MISMATCH " + str(bad)}')
    if a.so:
        cs = Path(a.so).read_bytes(); secs = sc.sections(cs)
        f = next((x for x in sc.candidate_functions(Path(a.so)) if x[2] == sym), None)
        if f:
            fb = sc.body(cs, secs, f[0], f[1])
            P('llc reproduces fastbuild:', norm_calls(fb) == norm_calls(cand), f'({len(fb)} vs {len(cand)})')
    P(f'{"fi":>4} {"T":>6} {"orig":>6} {"delta":>6} {"size":>5} {"al":>2} {"lt":>2} {"votes":>7}  name  [merged: ...]')
    for r in rep['rows']:
        mem = ' '.join(f'{nm}#{m}{"" if l else "*"}' for m, nm, l in r['members'])
        dl = f'{r["delta"]:+6d}' if r['delta'] is not None else '     ?'
        og = f'{r["orig"]:#6x}' if r['orig'] is not None else '     ?'
        flag = '' if confident(r, a.minv) else ' ~'
        P(f'{r["fi"]:>4} {r["T"]:#6x} {og} {dl} {r["size"]:>5} {r["align"]:>2} {r["lt"]:>2} {r["votes"]:>3}/{r["tot"]:<3} '
          f'{r["name"]}{"" if r["lt"] else "*"}{flag}' + (f'  [{mem}]' if mem else ''))
    P('\n# delta breaks (orig has DIFF more bytes between A and B):')
    for p, r, dd in breaks(rep['rows'], a.minv):
        P(f'  {dd:+5d} between fi{p["fi"]} {p["name"]} (T {p["T"]:#x}) and fi{r["fi"]} {r["name"]} (T {r["T"]:#x})')
    P('\n# original layout implied by confident objects (sorted by orig T); gaps = orig bytes ours does not place there')
    prevT = 0
    for r in sorted((r for r in rep['rows'] if confident(r, a.minv)), key=lambda r: (r['orig'], r['fi'])):
        lo = r['orig'] - r['size']
        gap = f'   gap {lo - prevT:+d}' if lo != prevT else ''
        P(f'  orig {lo:#6x}..{r["orig"]:#6x}  fi{r["fi"]:<4} {r["name"] or "-":28s} size {r["size"]:<4} ours T {r["T"]:#x}{gap}')
        prevT = max(prevT, r['orig'])
    if not a.no_partition:
        partition(a, mod_path, sym, d, orig, mm, final, names, lt, rep, P)
    if a.what_if:
        res = what_if(final, a.what_if); hit = tot = 0
        for r in rep['rows']:
            if confident(r, a.minv) and r['fi'] in res:
                tot += 1; hit += res[r['fi']] == r['orig']
        P(f'\n# what-if {a.what_if}: confident objects at implied orig T: {hit}/{tot} (now '
          f'{sum(1 for r in rep["rows"] if confident(r, a.minv) and r["delta"] == 0)})')
    if a.json:
        Path(a.json).write_text(json.dumps({k: v for k, v in rep.items() if k in ('ratio', 'pairs', 'offeq', 'rows', 'frame_orig', 'frame_cand')}, indent=1, default=str))


if __name__ == '__main__':
    main()
