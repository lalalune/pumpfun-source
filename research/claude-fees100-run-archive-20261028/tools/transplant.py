#!/usr/bin/env python3
"""DIAGNOSTIC ONLY (never harvested): transplant ORIGINAL function bodies into the candidate root object.

usage: python3 -I transplant.py --obj ROOT.rcgu.o --symbols CAND-symbols.so --map CAND.map --out NEW.o
                                [--windows 120816,147944,163920] [--report R.json]

For every listed original window, the candidate function placed at the same window position (the
layout recipe orders candidate functions by original window) has its object section content replaced
by the original window's bytes. Every call/lddw/syscall in the original body is re-expressed as an
ordinary object relocation against the candidate's corresponding symbol (call targets through the
positional window correspondence, data through the read-only section correspondence), so the real
linker re-resolves every address. Used to show what the whole ELF looks like once the remaining
bodies are equal. This copies original machine code: it is an analysis instrument, not a recipe.
"""
import argparse, bisect, collections, importlib.util, json, re, struct, sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import relobj
R = Path('/Users/shawwalters/fees100-run')
def module(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
w = module('wm', R / 'base/research/fees-composed-frontier188/window_map.py'); m = w.m
ORIG = (R / 'base/evidence/original/pump_fees/deployed.so').read_bytes()
MAPRE = re.compile(r'\s*([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+(\d+)\s+(\S+):\((\.[^)]*)\)\s*')

def map_sections(text):
    rows = []; cur_out = None
    for line in text.splitlines():
        mm = MAPRE.fullmatch(line)
        if mm:
            rows.append(dict(address=int(mm[1], 16), size=int(mm[3], 16), owner=mm[5], section=mm[6]))
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--obj', required=True); ap.add_argument('--symbols', required=True); ap.add_argument('--map', required=True)
    ap.add_argument('--out', required=True); ap.add_argument('--windows', default='120816,147944,163920'); ap.add_argument('--report')
    a = ap.parse_args()
    cimg = Path(a.symbols).read_bytes()
    obj = relobj.Obj(Path(a.obj).read_bytes())
    objname = Path(a.obj).name
    ow, cw = w.windows(ORIG), w.windows(cimg)
    o2c = {ow[i]['address']: cw[i]['address'] for i in range(len(ow))}
    cfun = collections.defaultdict(list)
    for f in m.functions(cimg): cfun[f['address']].append(f['name'])
    # original / candidate section geometry
    def secs(img): return {s['name']: s for s in m.elf_layout(img)['sections']}
    os_, cs = secs(ORIG), secs(cimg)
    def translate(v):
        for n in ('.rodata', '.data.rel.ro'):
            if os_[n]['address'] <= v < os_[n]['address'] + os_[n]['size']:
                return cs[n]['address'] + v - os_[n]['address'], n
        if os_['.text']['address'] <= v < os_['.text']['address'] + os_['.text']['size']:
            return o2c.get(v), '.text'
        return None, None
    # object symbol addresses through the map placement of root-object sections
    rows = map_sections(Path(a.map).read_text())
    placed = {}
    for r in rows:
        if r['owner'].endswith(objname) or r['owner'].split('/')[-1] == objname:
            placed[r['section']] = r['address']
    internal = [r for r in rows if r['owner'] == '<internal>']
    addr_sym = collections.defaultdict(list)
    for k, s in enumerate(obj.syms):
        if s['shndx'] in (0, 0xfff1, 0xfff2) or s['shndx'] >= len(obj.sh): continue
        sec = obj.sh[s['shndx']]['name']
        if sec in placed and (s['info'] & 15) in (0, 1, 2):
            addr_sym[placed[sec] + s['value']].append(k)
    # merged constants: content -> symbol (section .rodata.cstN)
    merged = collections.defaultdict(list)
    for k, s in enumerate(obj.syms):
        if s['shndx'] in (0, 0xfff1, 0xfff2) or s['shndx'] >= len(obj.sh): continue
        sh = obj.sh[s['shndx']]
        if sh['flags'] & 0x10 and sh['name'].startswith('.rodata.cst'):
            n = int(sh['name'][len('.rodata.cst'):])
            merged[(n, obj.contents[s['shndx']][s['value']:s['value'] + n])].append(k)
    name_idx = {}
    for k, s in enumerate(obj.syms):
        if s['name']: name_idx.setdefault(s['name'], k)
    added = []
    def sym_for_name(nm):
        if nm in name_idx: return name_idx[nm]
        obj.syms.append(dict(name_off=0, name=nm, info=(1 << 4) | 0, other=0, shndx=0, value=0, size=0))
        k = len(obj.syms) - 1; name_idx[nm] = k; added.append(nm); return k
    report = dict(windows=[], added_undefined=added)
    for wa in [int(x) for x in a.windows.split(',')]:
        i = next(j for j, r in enumerate(ow) if r['address'] == wa)
        o, c = ow[i], cw[i]
        names = cfun[c['address']]
        secname = next(('.text.' + n for n in names if '.text.' + n in obj.byname), None)
        assert secname, (wa, names)
        si = obj.byname[secname]
        body = bytearray(m.at_address(ORIG, o['address'], o['bytes']))
        orel = dict(m.relocations(ORIG)); odyn = w.dynamic_symbols(ORIG)
        rels = []; stats = collections.Counter(); unresolved = []
        p = 0
        while p < len(body):
            op = body[p]; width = 16 if op == 0x18 else 8; addr = o['address'] + p
            info = orel.get(addr, 0)
            if info & 0xffffffff == 10:
                nm = odyn[info >> 32]['name']; rels.append((p, 10, sym_for_name(nm))); stats['import:' + nm] += 1
                struct.pack_into('<i', body, p + 4, -1)
            elif op == 0x85 and (body[p + 1] >> 4) == 1:
                imm = struct.unpack_from('<i', body, p + 4)[0]; to = addr + 8 + imm * 8; tc = o2c.get(to)
                cands = [n for n in cfun.get(tc, []) if n in name_idx] or cfun.get(tc, [])
                if not cands: unresolved.append(('call', p, to)); p += width; continue
                rels.append((p, 10, sym_for_name(cands[0]))); stats['call'] += 1
                struct.pack_into('<i', body, p + 4, -1)
            elif op == 0x18 and info & 0xffffffff == 8:
                v = int.from_bytes(body[p + 4:p + 8] + body[p + 12:p + 16], 'little')
                vc, kind = translate(v)
                k = None
                if kind == '.text':
                    cands = [n for n in cfun.get(vc, []) if n in name_idx] or cfun.get(vc, [])
                    k = sym_for_name(cands[0]) if cands else None
                elif vc is not None:
                    ks = addr_sym.get(vc, [])
                    if ks: k = ks[0]
                    else:
                        for r in internal:
                            if r['address'] <= vc < r['address'] + r['size'] and r['section'].startswith('.rodata.cst'):
                                n = int(r['section'][len('.rodata.cst'):])
                                ks = merged.get((n, m.at_address(cimg, vc, n)), [])
                                if ks: k = ks[0]
                if k is None: unresolved.append(('lddw', p, v, vc, kind)); p += width; continue
                rels.append((p, 1, k)); stats['lddw:' + str(kind)] += 1
                body[p + 4:p + 8] = bytes(4); body[p + 12:p + 16] = bytes(4)
            p += width
        assert not unresolved, unresolved
        # install content + relocations
        obj.contents[si] = bytes(body)
        rj, _ = obj.rels(si)
        obj.contents[rj] = b''.join(struct.pack('<QQ', off, (k << 32) | t) for off, t, k in rels)
        for s in obj.syms:
            if s['shndx'] == si and (s['info'] & 15) == 2: s['size'] = len(body)
        report['windows'].append(dict(window=wa, section=secname, orig_bytes=len(body), cand_bytes=c['bytes'],
                                      relocations=len(rels), stats=dict(stats)))
    # added undefined symbols must be GLOBAL and after locals (appended at end: fine)
    Path(a.out).write_bytes(obj.serialize())
    if a.report: Path(a.report).write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1))

if __name__ == '__main__':
    main()
