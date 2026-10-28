#!/usr/bin/env python3
"""Disassemble SBF windows with symbolic call targets, for original/candidate alignment.

usage: python3 -I dis.py IMAGE ADDRESS [--names-from CANDIDATE_SYMBOLS.so] [--mask]
For the original image, call targets are named through unique normalized pairs with the names-from image.
--mask prints a normalized stream (no branch distances / stack offsets kept) for diffing.
"""
import argparse, importlib.util, re, sys
from pathlib import Path
sys.dont_write_bytecode = True
BASE = Path('/Users/shawwalters/fees100-run/base')
def module(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
w = module('wm', BASE / 'research/fees-composed-frontier188/window_map.py'); m = w.m
_meas = module('fees_measure', Path(__file__).resolve().parent / 'measure.py')
ALU = {0x00:'add',0x10:'sub',0x20:'mul',0x30:'div',0x40:'or',0x50:'and',0x60:'lsh',0x70:'rsh',0x80:'neg',0x90:'mod',0xa0:'xor',0xb0:'mov',0xc0:'arsh',0xd0:'end'}
JMP = {0x00:'ja',0x10:'jeq',0x20:'jgt',0x30:'jge',0x40:'jset',0x50:'jne',0x60:'jsgt',0x70:'jsge',0x80:'call',0x90:'exit',0xa0:'jlt',0xb0:'jle',0xc0:'jslt',0xd0:'jsle'}
SZ = {0x00:'w',0x08:'h',0x10:'b',0x18:'dw'}
def demangle(n):
    if not n: return n
    n = re.sub(r'17h[0-9a-f]{16}E$', '', n)
    out=[]; s=n[3:] if n.startswith('_ZN') else n; i=0
    while i < len(s) and s[i].isdigit():
        j=i
        while s[j].isdigit(): j+=1
        L=int(s[i:j]); out.append(s[j:j+L]); i=j+L
    if out: return '::'.join(out).replace('$LT$','<').replace('$GT$','>').replace('$u20$',' ').replace('..','::').replace('$RF$','&')
    return n
def names_for(image, ref=None):
    fn = {f['address']: f['name'] for f in m.functions(image)}
    if fn or ref is None: return fn
    o = _meas.windows(image); c = _meas.windows(ref); rf = {f['address']: f['name'] for f in m.functions(ref)}
    comp = w.compare(o, c); res = {}
    for p in comp['unique_pairs']:
        res[p['original']['address']] = rf.get(p['candidate']['address'])
    for g in comp['ambiguous']:
        nm = {rf.get(x['address']) for x in g['candidate']}
        for x in g['original']: res[x['address']] = '|'.join(sorted(n for n in nm if n))[:120] + ' (ambiguous)'
    return res
def listing(image, address, names, mask=False):
    win = {r['address']: r for r in _meas.windows(image)}[address]
    rel = dict(m.relocations(image)); dyn = w.dynamic_symbols(image)
    rows = m.instructions(image, address, win['bytes']); out = []
    for r in rows:
        op = r['opcode']; cls = op & 7; d = r['destination']; s = r['source']; off = r['displacement']; imm = r['immediate']
        a = address + r['offset']; info = rel.get(a, 0)
        if op == 0x18:
            v = r['lddw_value']
            if info & 0xffffffff == 8:
                try: preview = m.at_address(image, v, 24)
                except Exception: preview = b''
                txt = preview.split(b'\0')[0][:24]
                t = f'lddw r{d}, @ptr' + (f' "{txt.decode("latin1")}"' if mask else f' {v:#x} "{txt.decode("latin1")}"')
            else: t = f'lddw r{d}, {v:#x}'
        elif cls in (1,):
            t = f'ldx{SZ[op&0x18]} r{d}, [r{s}{"+" if off>=0 else ""}{"S" if (mask and s==10) else off}]'
        elif cls == 2:
            t = f'st{SZ[op&0x18]} [r{d}{"+" if off>=0 else ""}{"S" if (mask and d==10) else off}], {imm}'
        elif cls == 3:
            t = f'stx{SZ[op&0x18]} [r{d}{"+" if off>=0 else ""}{"S" if (mask and d==10) else off}], r{s}'
        elif cls in (4, 7):
            nm = ALU.get(op & 0xf0, f'alu{op:#x}') + ('32' if cls == 4 else '')
            src = f'r{s}' if op & 8 else str(imm)
            t = f'{nm} r{d}, {src}' if (op & 0xf0) != 0x80 else f'{nm} r{d}'
        elif cls in (5, 6):
            j = JMP.get(op & 0xf0, f'j{op:#x}')
            if j == 'call':
                if info & 0xffffffff == 10: t = f'call {dyn[info>>32]["name"]}'
                elif 'call_target' in r:
                    tg = r['call_target']; t = f'call {demangle(names.get(tg)) or hex(tg)}'
                else: t = f'syscall {imm:#x}'
            elif j == 'exit': t = 'exit'
            else:
                tgt = r['offset'] + 8 + off * 8
                src = f'r{s}' if op & 8 else str(imm)
                t = f'{j} r{d}, {src}, ->{"L" if mask else tgt}' if j != 'ja' else f'ja ->{"L" if mask else tgt}'
        else: t = f'?? {r["raw"]}'
        out.append((r['offset'], t))
    return out
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('image'); ap.add_argument('address', type=lambda x: int(x, 0))
    ap.add_argument('--names-from'); ap.add_argument('--mask', action='store_true')
    a = ap.parse_args(); img = Path(a.image).read_bytes()
    ref = Path(a.names_from).read_bytes() if a.names_from else None
    names = names_for(img, ref)
    for o, t in listing(img, a.address, names, a.mask): print(f'{o:6d}  {t}' if not a.mask else t)
