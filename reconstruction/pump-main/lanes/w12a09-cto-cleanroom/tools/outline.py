#!/usr/bin/env python3
"""Structural outline of admin_cto::execute (window 0x22a10): original vs a candidate.

  outline.py blocks [--side orig|cand] [--cand unstripped.so]   # basic blocks in layout order
  outline.py events [--side orig|cand] [--cand unstripped.so]   # linear event stream (calls/lines/errs/strs)
  outline.py align  [--cand unstripped.so]                      # difflib alignment of the two event streams
  outline.py frame  [--side orig|cand] [--cand unstripped.so]   # r10 offsets touched, first/last use
  outline.py dis --range 0x1c78-0x1d70 [--side orig|cand]      # annotated disassembly, offsets relative to start

Events per block: calls (symbolized through the candidate's symbol table: every other function
sits at the same address in both binaries, because both unmatched windows keep their size),
Source coordinates (line immediates), error-code immediates (2000..2999, 3000..3999, 6000..6299),
.rodata strings named by lddw (msg! texts, seeds), .data.rel.ro pointers (vtables), exits.
Default candidate = $C/w11/current-baseline/unstripped.so.
"""
import argparse, bisect, difflib, re, struct, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = next(p for p in HERE.parents if (p / 'reconstruction' / 'harness').is_dir())
H = ROOT / 'reconstruction' / 'harness'
sys.path.insert(0, str(H))
from score_admission import sections  # noqa: E402
from elf_symbols import function_symbols  # noqa: E402
from win import objdump_text, demangle  # noqa: E402

ORIG = ROOT / 'evidence/original/pump/deployed.so'
DEFAULT_CAND = Path.home() / '.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so'
W, WB = 0x22a10, 27400
JUMP = re.compile(r'^(ja|jeq|jne|jgt|jge|jlt|jle|jsgt|jsge|jslt|jsle|jset)\b')


def load(path):
    blob = Path(path).read_bytes()
    return blob, sections(blob)


def symtab(cand_blob):
    fs = sorted((a, s, demangle(n)) for a, s, n in function_symbols(cand_blob))
    return fs, [a for a, _, _ in fs]


def symname(fs, addrs, t):
    i = bisect.bisect_right(addrs, t) - 1
    if i < 0:
        return '?%#x' % t
    a, s, n = fs[i]
    n = re.sub(r'^pump_recovered::', '', n)
    return n if a == t else '%s+%#x' % (n, t - a)


def read_at(blob, secs, vaddr, n):
    for name, s in secs.items():
        if s['addr'] and s['addr'] <= vaddr < s['addr'] + s['size']:
            o = vaddr - s['addr'] + s['offset']
            return name, blob[o:o + n]
    return None, b''


def strat(blob, secs, vaddr):
    name, b = read_at(blob, secs, vaddr, 72)
    if name is None:
        return None
    if name == '.rodata':
        s = bytearray()
        for c in b:
            if 32 <= c < 127:
                s.append(c)
            else:
                break
        if len(s) >= 4:
            return '"%s"' % s.decode()[:48]
        return 'ro+%#x' % (vaddr - secs['.rodata']['addr'])
    return '%s+%#x' % (name, vaddr - secs[name]['addr'])


def disasm(path, start, size):
    rows = objdump_text(path, start, start + size)
    return sorted(rows.items())


def side(path, start, size, fs, addrs):
    blob, secs = load(path)
    ins = disasm(path, start, size)
    out = []
    for a, t in ins:
        t = re.sub(r'\s*<[^<>]*>$', '', t)
        ev = []
        m = re.match(r'^call (-?0x[0-9a-f]+|-?\d+)$', t)
        if m:
            imm = int(m.group(1), 0)
            ev.append(('call', 'SYSCALL' if imm == -1 else symname(fs, addrs, a + 8 + imm * 8)))
        m = re.match(r'^lddw r\d+, (0x[0-9a-f]+)$', t)
        if m:
            s = strat(blob, secs, int(m.group(1), 16))
            if s:
                ev.append(('str', s))
        m = re.match(r'^(?:stw|stdw|stb|sth) \[r10 - (0x[0-9a-f]+)\], (0x[0-9a-f]+)$', t) or \
            re.match(r'^mov(?:64|32) r\d+, (?:(0x[0-9a-f]+)|)(0x[0-9a-f]+)$', t)
        if m:
            v = int(m.group(2), 16)
            if 6000 <= v < 6300 or 2000 <= v < 2100 or 3000 <= v < 3100:
                ev.append(('err', v))
        if t == 'exit':
            ev.append(('exit', ''))
        out.append((a - start, t, ev))
    return out, blob, secs


def coord_lines(path, start, size):
    """Source sites through the harness's coords.sites; returns {offset: line}."""
    import coords
    blob, secs = load(path)
    o = start - secs['.text']['addr'] + secs['.text']['offset']
    return {s['slot']: s['line'] for s in coords.sites(blob, secs, start, blob[o:o + size])
            if s['path'].endswith('admin_cto.rs')}


def blocks(ins):
    n = len(ins)
    offs = [o for o, _, _ in ins]
    idx = {o: k for k, o in enumerate(offs)}
    leaders = {0}
    succ = {}
    for k, (o, t, _) in enumerate(ins):
        size = (ins[k + 1][0] - o) if k + 1 < n else 8
        if JUMP.match(t):
            m = re.search(r'([+-]0x[0-9a-f]+|[+-]\d+)$', t)
            tgt = o + 8 + int(m.group(1), 0) * 8
            leaders.add(tgt)
            if k + 1 < n:
                leaders.add(ins[k + 1][0])
        elif t == 'exit' and k + 1 < n:
            leaders.add(ins[k + 1][0])
    ls = sorted(x for x in leaders if x in idx)
    bl = []
    for i, L in enumerate(ls):
        end = ls[i + 1] if i + 1 < len(ls) else ins[-1][0] + 8
        body = [x for x in ins[idx[L]:] if x[0] < end]
        last = body[-1][1]
        ss = []
        if JUMP.match(last):
            m = re.search(r'([+-]0x[0-9a-f]+|[+-]\d+)$', last)
            tgt = body[-1][0] + 8 + int(m.group(1), 0) * 8
            if not last.startswith('ja '):
                ss.append(end)
            ss.append(tgt)
        elif last != 'exit':
            ss.append(end)
        bl.append({'start': L, 'end': end, 'ins': body, 'succ': ss})
    num = {b['start']: i for i, b in enumerate(bl)}
    preds = {i: [] for i in range(len(bl))}
    for i, b in enumerate(bl):
        b['succ'] = [num.get(s, -1) for s in b['succ']]
        for s in b['succ']:
            if s >= 0:
                preds[s].append(i)
    for i, b in enumerate(bl):
        b['preds'] = preds[i]
    return bl


def get(sidename, cand):
    cblob = Path(cand).read_bytes()
    fs, addrs = symtab(cblob)
    if sidename == 'orig':
        path, start, size = ORIG, W, WB
    else:
        hit = [(a, s) for a, s, n in fs if re.search(r'admin_cto::execute$', n)]
        path, (start, size) = cand, hit[0]
    ins, blob, secs = side(path, start, size, fs, addrs)
    lines = coord_lines(path, start, size)
    # attach Source lines to the instruction that stores the line immediate's descriptor
    for k, (o, t, ev) in enumerate(ins):
        if o in lines:
            ev.insert(0, ('line', lines[o]))
    return ins


def fmt_ev(ev):
    k, v = ev
    if k == 'call':
        v = re.sub(r'::h[0-9a-f]{16}', '', v)
        v = re.sub(r'<[^<>]*(<[^<>]*(<[^<>]*>[^<>]*)*>[^<>]*)*>', '<..>', v) if len(v) > 90 else v
        return 'call ' + v[:110]
    if k == 'err':
        return 'err %d' % v
    if k == 'line':
        return 'LINE %d' % v
    if k == 'str':
        return 'str ' + v
    return k


def stores(body):
    st = set()
    for o, t, _ in body:
        m = re.match(r'^st[xb]?[bhwd]* \[r10 - (0x[0-9a-f]+)\]', t)
        if m:
            st.add(int(m.group(1), 16))
    return st


def cmd_blocks(ins):
    for i, b in enumerate(blocks(ins)):
        evs = [fmt_ev(e) for _, _, ev in b['ins'] for e in ev]
        n = sum(1 for _ in b['ins'])
        st = stores(b['ins'])
        print('B%-3d %#06x-%#06x %3di preds=%s succ=%s st=%d %s' % (
            i, b['start'], b['end'], n, ','.join(map(str, b['preds'][:6])) + ('..' if len(b['preds']) > 6 else ''),
            ','.join(map(str, b['succ'])), len(st), b['ins'][-1][1] if JUMP.match(b['ins'][-1][1]) else ''))
        for e in evs:
            print('        ' + e)


def stream(ins):
    out = []
    for o, t, ev in ins:
        for e in ev:
            if e[0] == 'exit':
                continue
            out.append((o, fmt_ev(e)))
    return out


def cmd_events(ins):
    for o, e in stream(ins):
        print('%#06x %s' % (o, e))


def cmd_align(oi, ci):
    a, b = stream(oi), stream(ci)
    ka = [e for _, e in a]
    kb = [e for _, e in b]
    sm = difflib.SequenceMatcher(None, ka, kb, autojunk=False)
    print('# event-stream ratio %.4f (orig %d events, cand %d)' % (sm.ratio(), len(ka), len(kb)))
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for i, j in zip(range(i1, i2), range(j1, j2)):
                print('  %#06x %#06x   %s' % (a[i][0], b[j][0], ka[i]))
        else:
            for i in range(i1, i2):
                print('- %#06x          %s' % (a[i][0], ka[i]))
            for j in range(j1, j2):
                print('+        %#06x   %s' % (b[j][0], kb[j]))


def cmd_frame(ins):
    first, last, cnt = {}, {}, {}
    for o, t, _ in ins:
        for m in re.finditer(r'\[r10 - (0x[0-9a-f]+)\]', t):
            x = int(m.group(1), 16)
            first.setdefault(x, o); last[x] = o; cnt[x] = cnt.get(x, 0) + 1
    for x in sorted(first, reverse=True):
        print('-%#06x first %#06x last %#06x n=%d' % (x, first[x], last[x], cnt[x]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['blocks', 'events', 'align', 'frame', 'dis'])
    ap.add_argument('--range', default='0x0-0x7000', help='dis: relative offset range a-b')
    ap.add_argument('--side', choices=['orig', 'cand'], default='orig')
    ap.add_argument('--cand', default=str(DEFAULT_CAND))
    a = ap.parse_args()
    if a.cmd == 'align':
        cmd_align(get('orig', a.cand), get('cand', a.cand))
        return
    ins = get(a.side, a.cand)
    if a.cmd == 'dis':
        lo, hi = (int(x, 16) for x in a.range.split('-'))
        for o, t, ev in ins:
            if lo <= o < hi:
                print('%#06x %s%s' % (o, t, ('   ; ' + ', '.join(fmt_ev(e) for e in ev)) if ev else ''))
        return
    {'blocks': cmd_blocks, 'events': cmd_events, 'frame': cmd_frame}[a.cmd](ins)


if __name__ == '__main__':
    main()
