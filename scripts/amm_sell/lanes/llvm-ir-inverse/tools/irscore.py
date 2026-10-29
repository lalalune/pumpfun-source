#!/usr/bin/env python3
"""Score the sell cashback function inside an UNLINKED object (llc output) against the original.

irscore.py OBJ [--json] [--diff]
Masks call immediates and lddw values (relocations); checks callee-name sequence separately.
"""
import difflib, json, struct, subprocess, sys, re
from pathlib import Path

SW = Path('/Users/shawwalters/Documents/Codex/2026-10-24/amm-sell-swarm')
sys.path.insert(0, str(SW / 'harness'))
import elf_reader, sell_score  # noqa
B = SW / 'infra/sdk-native/rust/lib/rustlib/aarch64-apple-darwin/bin'
SYM = '_ZN18pump_amm_recovered12instructions4swap4sell8cashback17hccb72da5245169afE'
_orig = None


def original():
    global _orig
    if _orig is None:
        o = elf_reader.Elf(SW / 'infra/original/deployed.so')
        s = elf_reader.Elf(SW / 'baselines/baseline-build/symbols.so')
        names = {f['start']: f['name'] for f in s.funcs}
        code = o.b[0x4c750:0x4c750 + 9024]
        calls = []
        for off, ln, raw, text, f in sell_score.decode(o.b, 0x4c750, 9024):
            if f[0] == 'call':
                calls.append(names.get(0x4c750 + off + 8 + f[2] * 8, '?'))
        _orig = (code, calls)
    return _orig


def obj_func(obj, sym=SYM):
    tmp = Path(obj).with_suffix('.cb.bin')
    subprocess.run([str(B / 'llvm-objcopy'), '-O', 'binary', f'--only-section=.text.{sym}', str(obj), str(tmp)], check=True)
    code = tmp.read_bytes()
    out = subprocess.run([str(B / 'llvm-readobj'), '-r', str(obj)], capture_output=True, text=True).stdout
    rel = {}
    on = False
    for line in out.splitlines():
        if line.strip().startswith('Section (') and f'.rel.text.{sym} ' in line + ' ':
            on = True
            continue
        if on:
            if line.strip() == '}':
                break
            m = re.match(r'\s*0x([0-9A-Fa-f]+) (\S+) (\S+)', line)
            if m:
                rel[int(m.group(1), 16)] = m.group(3)
    calls = []
    for off, ln, raw, text, f in sell_score.decode(code, 0, len(code)):
        if f[0] == 'call':
            calls.append(rel.get(off, f'imm{f[2]}'))
    return code, calls


def mask(code):
    b = bytearray(code)
    at = 0
    while at < len(b):
        op = b[at]
        if op == 0x18:
            b[at + 4:at + 8] = bytes(4); b[at + 12:at + 16] = bytes(4); at += 16; continue
        if op == 0x85:
            b[at + 4:at + 8] = bytes(4)
        at += 8
    return bytes(b)


def tokens(code):
    rows = []
    for off, ln, raw, text, f in sell_score.decode(code, 0, len(code)):
        tgt = None
        if f[0] == 'ja' or (f[0].startswith('j') and len(f) == 5):
            tgt = off + ln + f[-1] * 8
        rows.append((off, f, tgt, text))
    targets = sorted({r[2] for r in rows if r[2] is not None})
    lab = {t: f'L{i}' for i, t in enumerate(targets)}
    toks = []
    for off, f, tgt, text in rows:
        if tgt is not None:
            toks.append(' '.join(map(str, f[:-1])) + ' ->' + lab[tgt])
        elif f[0] == 'call':
            toks.append('call')
        elif f[0] == 'lddw':
            toks.append(f'lddw {f[1]}')
        else:
            toks.append(' '.join(map(str, f)))
    return rows, toks


def score(obj, want_diff=False):
    ocode, ocalls = original()
    ccode, ccalls = obj_func(obj)
    mo, mc = mask(ocode), mask(ccode)
    orow, otok = tokens(ocode)
    crow, ctok = tokens(ccode)
    m = difflib.SequenceMatcher(None, otok, ctok, autojunk=False)
    ops = m.get_opcodes()
    dist = sum(max(i2 - i1, j2 - j1) for t, i1, i2, j1, j2 in ops if t != 'equal')
    slots = sum(1 for i in range(0, min(len(mo), len(mc)), 8) if mo[i:i + 8] != mc[i:i + 8])
    # how calls map: compare mangled names (original names from baseline symbols.so)
    calls_eq = [a == b for a, b in zip(ocalls, ccalls)]
    r = {'size': len(ccode), 'masked_equal': mo == mc, 'distance': dist, 'slot_diffs': slots,
         'calls_equal': len(ocalls) == len(ccalls) and all(calls_eq), 'ncalls': len(ccalls)}
    if want_diff:
        lines = []
        for t, i1, i2, j1, j2 in ops:
            if t == 'equal':
                continue
            for k in range(i1, i2):
                lines.append(f'- {orow[k][0]:#06x}         {orow[k][3]}')
            for k in range(j1, j2):
                lines.append(f'+        {crow[k][0]:#06x}  {crow[k][3]}')
            lines.append('')
        r['diff'] = lines
    return r


if __name__ == '__main__':
    r = score(sys.argv[1], '--diff' in sys.argv)
    d = r.pop('diff', None)
    print(json.dumps(r))
    if d:
        print('\n'.join(d))
