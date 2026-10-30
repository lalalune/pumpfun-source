#!/usr/bin/env python3
"""Window analysis for main-Pump byte matching.

  win.py list   [--cand unstripped.so] [--all] [--top N]   # unmatched windows + best-similar candidate fn
  win.py show   <orig_start> [--cand unstripped.so] [--sym REGEX] [--context N] [--full]
  win.py orig   <orig_start>                                # original disassembly only
  win.py sym    REGEX [--cand unstripped.so]                # list candidate fns matching REGEX (addr,size,name)

Diff tokens use the scorer's normalization (internal call imm + section-pointer lddw masked).
'-' = original only, '+' = candidate only. Default candidate = base/current/unstripped.so.
"""
import argparse, difflib, re, subprocess, sys
from pathlib import Path
from collections import Counter
from llvm_tools import objdump

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
from score import sections, normalize, body, original_windows, score, BASE  # noqa
from instruction_stream import instruction_offsets
from elf_symbols import function_symbols



def demangle(s):
    m = re.match(r'^_ZN(.*)E$', s)
    if not m:
        return s
    rest, parts = m.group(1), []
    while rest and rest[0].isdigit():
        n = re.match(r'^(\d+)', rest).group(1); rest = rest[len(n):]
        part = rest[:int(n)]
        parts.append(part[1:] if part.startswith('_$') else part)
        rest = rest[int(n):]
    if parts and re.fullmatch(r'h[0-9a-f]{16}', parts[-1]):
        parts = parts[:-1]
    t = '::'.join(parts)
    for a, b in [('$LT$', '<'), ('$GT$', '>'), ('$RF$', '&'), ('$BP$', '*'), ('$C$', ','), ('$u20$', ' '),
                 ('$u27$', "'"), ('$u5b$', '['), ('$u5d$', ']'), ('$u7b$', '{'), ('$u7d$', '}'), ('$u3b$', ';'),
                 ('$u2b$', '+'), ('$u22$', '"'), ('$LP$', '('), ('$RP$', ')'), ('..', '::'), ('$u7e$', '~')]:
        t = t.replace(a, b)
    return t


def insns(raw, addr, secs):
    norm = normalize(raw, addr, secs)
    i = 0; out = []
    while i < len(raw):
        n = 16 if raw[i] == 0x18 else 8
        out.append((addr + i, raw[i:i + n], norm[i:i + n])); i += n
    return out


def objdump_text(path, start, end):
    txt = subprocess.check_output([objdump(), '-d', '--no-show-raw-insn', f'--start-address={start:#x}', f'--stop-address={end:#x}', str(path)], text=True)
    d = {}
    for line in txt.splitlines():
        m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', line)
        if m:
            d[int(m.group(1), 16)] = re.sub(r'\s+<\.text\+0x[0-9a-f]+>', '', m.group(2).strip())
    return d


class Cand:
    def __init__(self, path):
        self.path = Path(path); self.blob = self.path.read_bytes(); self.secs = sections(self.blob)
        self.funcs = function_symbols(self.blob)
        self._opgrams = {}
        self._tokens = {}

    def fn(self, start, size):
        return body(self.blob, self.secs, start, size)

    def grams(self, start, size):
        key = (start, size)
        if key not in self._opgrams:
            self._opgrams[key] = opgrams(self.fn(start, size))
        return self._opgrams[key]

    def tokens(self, start, size):
        key = (start, size)
        if key not in self._tokens:
            self._tokens[key] = tuple(x[2] for x in insns(self.fn(start, size), start, self.secs))
        return self._tokens[key]


def opgrams(raw, k=3):
    ops = [raw[i] for i in instruction_offsets(raw)]
    return Counter(tuple(ops[i:i + k]) for i in range(max(0, len(ops) - k + 1)))


from original_input import resolve_original
ORIG = resolve_original(BASE / 'original.so').read_bytes(); ORIG_SECS = sections(ORIG)


def best_candidates(w, cand, top=3):
    og = opgrams(w['raw'])
    scored = []
    for (s, n, name) in cand.funcs:
        if not (0.4 * w['bytes'] <= n <= 2.5 * w['bytes']):
            continue
        cg = cand.grams(s, n); inter = sum((og & cg).values()); uni = sum((og | cg).values()) or 1
        scored.append((inter / uni, s, n, name))
    scored.sort(reverse=True)
    res = []
    orig_tok = [x[2] for x in insns(w['raw'], w['start'], ORIG_SECS)]
    # Keep the usual eight-way shortlist, but do not silently cap --top N.
    for j, s, n, name in scored[:max(8, top)]:
        ct = cand.tokens(s, n)
        res.append((difflib.SequenceMatcher(None, orig_tok, ct, autojunk=False).ratio(), j, s, n, name))
    res.sort(reverse=True)
    return res[:top]


def cmd_list(a):
    cand = Cand(a.cand); cur = score(a.cand); rows = []
    for w in original_windows():
        if cur[w['start']]['normalized'] and not a.all:
            continue
        bc = best_candidates(w, cand, 1)
        if bc:
            r, j, s, n, name = bc[0]; rows.append((w['start'], w['bytes'], r, s, n, demangle(name)))
        else:
            rows.append((w['start'], w['bytes'], 0, 0, 0, '?'))
    rows.sort(key=lambda x: -x[2])
    for st, b, r, s, n, name in rows[:a.top]:
        print(f"{st:#08x} {b:6d}B  best={r:.3f} cand@{s:#x} {n:6d}B  {name}")


def find_window(text):
    """Return (start, window) for an original window start, or exit 2 with a message."""
    try:
        st = int(text, 0)
    except ValueError:
        print(f'win.py: error: {text!r} is not a numeric address (e.g. 0x14f4e0)', file=sys.stderr); sys.exit(2)
    w = next((x for x in original_windows() if x['start'] == st), None)
    if w is None:
        print(f'win.py: error: {st:#x} is not an original window start (see `win.py list --all`)', file=sys.stderr); sys.exit(2)
    return st, w


def cmd_show(a):
    st, w = find_window(a.start)
    cand = Cand(a.cand)
    if a.sym:
        cs = [(s, n, nm) for (s, n, nm) in cand.funcs if re.search(a.sym, nm) or re.search(a.sym, demangle(nm))]
        if not cs:
            sys.exit('no candidate symbol matches')
        ot = [x[2] for x in insns(w['raw'], st, ORIG_SECS)]; best = []
        for s, n, nm in cs:
            ct = [x[2] for x in insns(cand.fn(s, n), s, cand.secs)]
            best.append((difflib.SequenceMatcher(None, ot, ct, autojunk=False).ratio(), 0, s, n, nm))
        best.sort(reverse=True)
    else:
        best = best_candidates(w, cand, 3)
    if not best:
        sys.exit('no candidate function in the requested window search scope')
    print(f"original window {st:#x}..{st + w['bytes']:#x} ({w['bytes']} B, {w['bytes'] // 8} slots)")
    for r, j, s, n, nm in best:
        print(f"  cand {s:#x} {n:6d}B ratio={r:.4f}  {demangle(nm)}")
    r, j, s, n, nm = best[0]
    oi = insns(w['raw'], st, ORIG_SECS); ci = insns(cand.fn(s, n), s, cand.secs)
    ot = objdump_text(resolve_original(BASE / 'original.so'), st, st + w['bytes']); ctx = objdump_text(cand.path, s, s + n)
    sm = difflib.SequenceMatcher(None, [x[2] for x in oi], [x[2] for x in ci], autojunk=False)
    print(f"\n--- diff vs {demangle(nm)} @ {s:#x} (ratio {sm.ratio():.4f}; '-' original, '+' candidate)")
    C = a.context
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            span = range(i2 - i1)
            if not a.full and i2 - i1 > 2 * C:
                for k in range(C):
                    print(f"  {oi[i1 + k][0]:#07x} {ci[j1 + k][0]:#07x}  {ot.get(oi[i1 + k][0], '')}")
                print(f"  ... {i2 - i1 - 2 * C} equal ...")
                span = range(i2 - i1 - C, i2 - i1)
            for k in span:
                print(f"  {oi[i1 + k][0]:#07x} {ci[j1 + k][0]:#07x}  {ot.get(oi[i1 + k][0], '')}")
            continue
        for k in range(i1, i2):
            print(f"- {oi[k][0]:#07x}          {ot.get(oi[k][0], '')}")
        for k in range(j1, j2):
            print(f"+         {ci[k][0]:#07x}  {ctx.get(ci[k][0], '')}")


def cmd_orig(a):
    st, w = find_window(a.start)
    for ad, t in objdump_text(resolve_original(BASE / 'original.so'), st, st + w['bytes']).items():
        print(f"{ad:#07x}  {t}")


def cmd_sym(a):
    cand = Cand(a.cand)
    for s, n, nm in cand.funcs:
        d = demangle(nm)
        if re.search(a.regex, nm) or re.search(a.regex, d):
            print(f"{s:#08x} {n:6d}  {d}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('list'); p.add_argument('--cand', type=Path, default=BASE / 'current/unstripped.so'); p.add_argument('--all', action='store_true'); p.add_argument('--top', type=int, default=10000)
    p = sub.add_parser('show'); p.add_argument('start'); p.add_argument('--cand', type=Path, default=BASE / 'current/unstripped.so'); p.add_argument('--sym'); p.add_argument('--context', type=int, default=3); p.add_argument('--full', action='store_true')
    p = sub.add_parser('orig'); p.add_argument('start')
    p = sub.add_parser('sym'); p.add_argument('regex'); p.add_argument('--cand', type=Path, default=BASE / 'current/unstripped.so')
    a = ap.parse_args()
    if getattr(a, 'top', 0) < 0 or getattr(a, 'context', 0) < 0:
        ap.error('--top and --context must be nonnegative')
    pattern = getattr(a, 'sym', None) if a.cmd == 'show' else getattr(a, 'regex', None)
    if pattern is not None:
        try:
            re.compile(pattern)
        except re.error as error:
            ap.error(f'invalid symbol regex: {error}')
    {'list': cmd_list, 'show': cmd_show, 'orig': cmd_orig, 'sym': cmd_sym}[a.cmd](a)
