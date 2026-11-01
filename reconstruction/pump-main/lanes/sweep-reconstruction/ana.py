#!/usr/bin/env python3
"""Annotated block listing / call sequence for one original window and one candidate function.

  ana.py orig  [--start 0x72810]                       # annotated original listing
  ana.py cand  <unstripped.so> [--sym REGEX]            # annotated candidate listing
  ana.py calls <unstripped.so> [--sym REGEX]            # side-by-side callee sequences
  ana.py blocks <unstripped.so> [--sym REGEX]           # block summaries (both)

Call names: original targets are resolved through the baseline score.json (window -> matched
candidate symbols); candidate targets through the candidate symbol table.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

TOOLS = Path('./worktrees/restore/reconstruction')
sys.path.insert(0, str(TOOLS / 'harness'))
from score import sections, candidate_functions, original_windows, BASE  # noqa
from win import demangle  # noqa

OBJDUMP = str(Path.home() / '.cache/solana/v1.52/platform-tools/llvm/bin/llvm-objdump')
BASELINE = Path.home() / '.cache/pumpfun-reconstruction/baseline-main-d2cb88d'
WSTART = 0x72810
WBYTES = 7832


def short(name):
    d = demangle(name)
    d = re.sub(r'pump_recovered::', '', d)
    d = re.sub(r'anchor_lang::', 'al::', d)
    d = re.sub(r'solana_program::', 'sp::', d)
    return d[:110]


def orig_names():
    sc = json.loads((BASELINE / 'score.json').read_text())['windows']
    m = {}
    for k, v in sc.items():
        if v['symbols']:
            m[int(k)] = short(v['symbols'][0])
        else:
            m[int(k)] = f'<unmatched window {int(k):#x}>'
    return m


def cand_names(path):
    return {s: short(n) for s, n, nm in [(a, n, n) for a, _, n in candidate_functions(path)]}


def objdump(path, start, end):
    txt = subprocess.check_output([OBJDUMP, '-d', '--no-show-raw-insn', f'--start-address={start:#x}',
                                   f'--stop-address={end:#x}', str(path)], text=True)
    rows = []
    for line in txt.splitlines():
        m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', line)
        if m:
            t = re.sub(r'\s+<[^>]*>', '', m.group(2).strip())
            rows.append((int(m.group(1), 16), t))
    return rows


JUMP = re.compile(r'^(j[a-z]+)\s+(?:.*,\s*)?([+-]0x[0-9a-f]+|[+-]\d+)$')
CALL = re.compile(r'^call\s+([+-]?0x[0-9a-f]+|[+-]?\d+)$')


def parse(rows, names, base):
    addrs = [a for a, _ in rows]
    nxt = {a: (addrs[i + 1] if i + 1 < len(addrs) else None) for i, a in enumerate(addrs)}
    ins = []
    leaders = {addrs[0]}
    for a, t in rows:
        e = {'addr': a, 'off': a - base, 'text': t}
        m = JUMP.match(t)
        if m:
            tgt = a + 8 + int(m.group(2), 0) * 8
            e['jump'] = (m.group(1), tgt)
            leaders.add(tgt)
            if nxt[a] is not None:
                leaders.add(nxt[a])
        elif t == 'exit':
            e['exit'] = True
            if nxt[a] is not None:
                leaders.add(nxt[a])
        m = CALL.match(t)
        if m:
            tgt = a + 8 + int(m.group(1), 0) * 8
            e['call'] = tgt
            e['callname'] = names.get(tgt, f'?{tgt:#x}')
        elif t.startswith('call') or t.startswith('syscall'):
            e['callname'] = t
        ins.append(e)
    return ins, sorted(leaders)


def blocks(ins, leaders, base):
    ls = set(leaders)
    out = []
    cur = None
    for e in ins:
        if e['addr'] in ls or cur is None:
            cur = {'start': e['addr'], 'off': e['addr'] - base, 'ins': []}
            out.append(cur)
        cur['ins'].append(e)
    return out


def load_orig(start=WSTART):
    w = next(x for x in original_windows() if x['start'] == start)
    rows = objdump(BASE / 'original.so', start, start + w['bytes'])
    ins, leaders = parse(rows, orig_names(), start)
    return ins, leaders, blocks(ins, leaders, start)


def load_cand(path, sym):
    funcs = candidate_functions(path)
    cs = [(s, n, nm) for s, n, nm in funcs if re.search(sym, nm) or re.search(sym, demangle(nm))]
    if not cs:
        sys.exit('no symbol')
    s, n, nm = cs[0]
    rows = objdump(path, s, s + n)
    ins, leaders = parse(rows, cand_names(path), s)
    return ins, leaders, blocks(ins, leaders, s), (s, n, nm)


def fmt_block(b):
    lines = [f"--- block +{b['off']:#06x} ({len(b['ins'])} ins)"]
    for e in b['ins']:
        t = e['text']
        extra = ''
        if 'callname' in e:
            extra = '   ; ' + e['callname']
        if 'jump' in e:
            extra = f"   ; -> +{e['jump'][1] - (e['addr'] - e['off']):#06x}"
        lines.append(f"  +{e['off']:#06x}  {t}{extra}")
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd')
    ap.add_argument('cand', nargs='?')
    ap.add_argument('--sym', default=r'sweep.*execute')
    ap.add_argument('--start', default=hex(WSTART))
    a = ap.parse_args()
    if a.cmd == 'orig':
        ins, leaders, bl = load_orig(int(a.start, 0))
        for b in bl:
            print(fmt_block(b))
    elif a.cmd == 'cand':
        ins, leaders, bl, meta = load_cand(a.cand, a.sym)
        print(f'# {meta[0]:#x} {meta[1]}B {demangle(meta[2])}')
        for b in bl:
            print(fmt_block(b))
    elif a.cmd == 'calls':
        oi, _, _ = load_orig(int(a.start, 0))
        ci, _, _, meta = load_cand(a.cand, a.sym)
        oc = [(e['off'], e['callname']) for e in oi if 'callname' in e]
        cc = [(e['off'], e['callname']) for e in ci if 'callname' in e]
        import difflib
        sm = difflib.SequenceMatcher(None, [c[1] for c in oc], [c[1] for c in cc], autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            for k in range(max(i2 - i1, j2 - j1)):
                l = oc[i1 + k] if i1 + k < i2 else None
                r = cc[j1 + k] if j1 + k < j2 else None
                ls = f'+{l[0]:#06x} {l[1]}' if l else ''
                rs = f'+{r[0]:#06x} {r[1]}' if r else ''
                mark = ' ' if op == 'equal' else '*'
                print(f'{mark} {ls:<70.70} | {rs}')
        print(f'# orig calls {len(oc)} cand calls {len(cc)}')
    elif a.cmd == 'blocks':
        for label, bl in (('ORIG', load_orig(int(a.start, 0))[2]), ('CAND', load_cand(a.cand, a.sym)[2])):
            print(f'==== {label} {len(bl)} blocks')
            for b in bl:
                last = b['ins'][-1]
                term = last['text'] if ('jump' in last or 'exit' in last) else 'fall'
                calls = [e['callname'].split('::')[-1][:40] for e in b['ins'] if 'callname' in e]
                print(f"  +{b['off']:#06x} n={len(b['ins']):3d} {term[:30]:<30} {calls}")


if __name__ == '__main__':
    main()
