#!/usr/bin/env python3
"""layout-elf lane: complete whole-ELF inventory of a stripped Fees candidate against the original.

usage: python3 -I elfinv.py CANDIDATE.so [--symbols SYMBOLS.so] [--json OUT.json] [--quiet]

Every byte of the original meaningful ELF extent is accounted for. Candidate addresses are translated
to original addresses through the positional window correspondence (the layout recipe places the
candidate's functions in original window order; the extra candidate function(s) follow the 585),
and the read-only sections through their section shifts. Under that translation each difference is
classified as
  (a) CONSEQUENCE  - explained only by the unmatched bodies' sizes/contents (address shifts,
                     relocation counts inside unmatched bodies, the extra outlined function), or
  (b) INDEPENDENT  - a difference that survives the translation (recipe/linker/symbol-order/data).
The run prints both lists; an end state is whole-ELF identical iff (b) is empty and the unmatched
bodies (and their relocations/targets) become equal.
"""
import argparse, bisect, collections, hashlib, importlib.util, json, struct, sys
from pathlib import Path
sys.dont_write_bytecode = True
BASE = Path('/Users/shawwalters/fees100-run/base')
def module(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
w = module('wm', BASE / 'research/fees-composed-frontier188/window_map.py'); m = w.m
ORIG_PATH = BASE / 'evidence/original/pump_fees/deployed.so'
sha = lambda b: hashlib.sha256(b).hexdigest()

DT = {0: 'NULL', 5: 'STRTAB', 6: 'SYMTAB', 10: 'STRSZ', 11: 'SYMENT', 17: 'REL', 18: 'RELSZ', 19: 'RELENT',
      22: 'TEXTREL', 30: 'FLAGS', 0x6ffffffa: 'RELCOUNT', 0x6ffffffb: 'FLAGS_1'}

def parse(img):
    e = {}
    (e['type'], e['machine'], e['version'], e['entry'], e['phoff'], e['shoff'], e['flags'], e['ehsize'],
     e['phentsize'], e['phnum'], e['shentsize'], e['shnum'], e['shstrndx']) = struct.unpack_from('<HHIQQQIHHHHHH', img, 16)
    e['ident'] = img[:16].hex()
    ph = [dict(zip(('type', 'flags', 'offset', 'vaddr', 'paddr', 'filesz', 'memsz', 'align'),
                   struct.unpack_from('<IIQQQQQQ', img, e['phoff'] + i * e['phentsize']))) for i in range(e['phnum'])]
    sh = [dict(zip(('name_off', 'type', 'flags', 'addr', 'offset', 'size', 'link', 'info', 'align', 'entsize'),
                   struct.unpack_from('<IIQQQQIIQQ', img, e['shoff'] + i * e['shentsize']))) for i in range(e['shnum'])]
    strtab = sh[e['shstrndx']]
    for s in sh:
        s['name'] = img[strtab['offset'] + s['name_off']:].split(b'\0', 1)[0].decode()
    secs = {s['name']: s for s in sh}
    data = lambda n: img[secs[n]['offset']:secs[n]['offset'] + secs[n]['size']]
    dyn = []
    d = data('.dynamic')
    for i in range(0, len(d), 16):
        tag, val = struct.unpack_from('<qQ', d, i); dyn.append((tag, val))
    syms = []
    ds, dstr = data('.dynsym'), data('.dynstr')
    for i in range(0, len(ds), 24):
        nm, info, other, shndx, val, size = struct.unpack_from('<IBBHQQ', ds, i)
        syms.append(dict(name=dstr[nm:].split(b'\0', 1)[0].decode(), name_off=nm, info=info, other=other,
                         shndx=shndx, value=val, size=size))
    rel = []
    rd = data('.rel.dyn')
    for i in range(0, len(rd), 16):
        off, info = struct.unpack_from('<QQ', rd, i); rel.append((off, info & 0xffffffff, info >> 32))
    extent = max(e['shoff'] + e['shnum'] * e['shentsize'], max(s['offset'] + s['size'] for s in sh if s['type'] != 8))
    return dict(header=e, phdrs=ph, sections=sh, secs=secs, dynamic=dyn, dynsym=syms, rel=rel, extent=extent, data=data)

class Mapper:
    """candidate address -> original address (None when inside an unmatched/extra body)."""
    def __init__(self, O, C, ow, cw):
        self.pairs = []  # (cand_start, cand_end, orig_start, exact)
        for i, c in enumerate(cw):
            if i < len(ow):
                o = ow[i]
                self.pairs.append((c['address'], c['address'] + c['bytes'], o['address'], o['signature'] == c['signature'], o['bytes']))
            else:
                self.pairs.append((c['address'], c['address'] + c['bytes'], None, False, 0))
        self.starts = [p[0] for p in self.pairs]
        self.sec = []
        for n in ('.rodata', '.data.rel.ro', '.dynamic', '.dynsym', '.dynstr', '.rel.dyn'):
            cs, os_ = C['secs'][n], O['secs'][n]
            self.sec.append((cs['addr'], cs['addr'] + cs['size'], os_['addr'], n))
        self.text = (C['secs']['.text']['addr'], C['secs']['.text']['addr'] + C['secs']['.text']['size'])
    def text_pair(self, a):
        j = bisect.bisect_right(self.starts, a) - 1
        return self.pairs[j] if j >= 0 and a < self.pairs[j][1] else None
    def __call__(self, a, allow_function_start=True):
        if self.text[0] <= a < self.text[1]:
            p = self.text_pair(a)
            if p is None or p[2] is None: return None
            if a == p[0] and allow_function_start: return p[2]
            return p[2] + (a - p[0]) if p[3] else None
        for s, e_, o, n in self.sec:
            if s <= a < e_ or (a == e_ and n in ('.rodata', '.data.rel.ro')):
                return o + (a - s)
        return None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('candidate'); ap.add_argument('--symbols')
    ap.add_argument('--json'); ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args()
    oimg = ORIG_PATH.read_bytes(); cimg = Path(a.candidate).read_bytes()
    simg = Path(a.symbols).read_bytes() if a.symbols else None
    O, C = parse(oimg), parse(cimg)
    ow, cw = w.windows(oimg), w.windows(cimg)
    names = {}
    if simg:
        for f in m.functions(simg): names.setdefault(f['address'], f['name'])
    M = Mapper(O, C, ow, cw)
    A, B = [], []  # consequence / independent
    rep = collections.OrderedDict()
    oext = oimg[:O['extent']]
    rep['original'] = dict(file_bytes=len(oimg), elf_extent=O['extent'], tail_bytes=len(oimg) - O['extent'],
                           tail_all_zero=not any(oimg[O['extent']:]), sha256=sha(oimg), extent_sha256=sha(oext))
    rep['candidate'] = dict(file_bytes=len(cimg), elf_extent=C['extent'], sha256=sha(cimg),
                            equal_to_original_extent=cimg == oext)
    # ---- windows
    unmatched = [(i, ow[i], cw[i]) for i in range(min(len(ow), len(cw))) if ow[i]['signature'] != cw[i]['signature']]
    extra = cw[len(ow):]
    body_delta = sum(o['bytes'] - c['bytes'] for _, o, c in unmatched) - sum(x['bytes'] for x in extra)
    rep['windows'] = dict(original=len(ow), candidate=len(cw),
        positional_signature_equal=sum(1 for i in range(min(len(ow), len(cw))) if ow[i]['signature'] == cw[i]['signature']),
        unmatched=[dict(index=i, orig_addr=o['address'], orig_bytes=o['bytes'], cand_addr=c['address'], cand_bytes=c['bytes'],
                        delta=o['bytes'] - c['bytes'], name=names.get(c['address'])) for i, o, c in unmatched],
        extra=[dict(cand_addr=x['address'], bytes=x['bytes'], name=names.get(x['address'])) for x in extra],
        text_size_delta_from_bodies=body_delta)
    # ---- ELF header
    oh, ch = O['header'], C['header']
    hd = {}
    for k in oh:
        if oh[k] != ch[k]: hd[k] = (oh[k], ch[k])
    for k, (ov, cv) in hd.items():
        if k == 'entry':
            (A if M(cv) == ov else B).append(f'header.entry {ov:#x} vs {cv:#x} (translated {M(cv)})')
        elif k == 'shoff':
            exp = cv + (O['extent'] - C['extent'])
            (A if exp == ov else B).append(f'header.shoff {ov} vs {cv} (shift = meaningful size gap {O["extent"] - C["extent"]})')
        else:
            B.append(f'header.{k} {ov} vs {cv}')
    rep['header_diffs'] = hd
    # ---- section headers
    sd = []
    if [s['name'] for s in O['sections']] != [s['name'] for s in C['sections']]:
        B.append('section name/order differs: %s vs %s' % ([s['name'] for s in O['sections']], [s['name'] for s in C['sections']]))
    for so, sc in zip(O['sections'], C['sections']):
        for k in ('name_off', 'type', 'flags', 'addr', 'offset', 'size', 'link', 'info', 'align', 'entsize'):
            if so[k] != sc[k]:
                sd.append((so['name'], k, so[k], sc[k]))
    rep['section_header_diffs'] = sd
    text_gap = O['secs']['.text']['size'] - C['secs']['.text']['size']
    rel_gap = O['secs']['.rel.dyn']['size'] - C['secs']['.rel.dyn']['size']
    for n, k, ov, cv in sd:
        if n == '.text' and k == 'size':
            (A if ov - cv == body_delta else B).append(f'.text size {ov} vs {cv}: gap {ov - cv} == unmatched body delta {body_delta}')
        elif k in ('addr', 'offset') and n in ('.rodata', '.data.rel.ro', '.dynamic', '.dynsym', '.dynstr', '.rel.dyn'):
            (A if ov - cv == text_gap else B).append(f'{n}.{k} shifted by {ov - cv} (text gap {text_gap})')
        elif n == '.rel.dyn' and k == 'size':
            A.append(f'.rel.dyn size {ov} vs {cv} ({rel_gap // 16} relocation entries; checked below)')
        elif n == '.shstrtab' and k == 'offset':
            (A if ov - cv == text_gap + rel_gap else B).append(f'.shstrtab offset shift {ov - cv} = text gap + rel gap')
        else:
            B.append(f'section {n}.{k} {ov} vs {cv}')
    # ---- program headers
    pd = []
    for i, (po, pc) in enumerate(zip(O['phdrs'], C['phdrs'])):
        for k in po:
            if po[k] != pc[k]: pd.append((i, k, po[k], pc[k]))
    if len(O['phdrs']) != len(C['phdrs']): B.append('program header count differs')
    rep['program_header_diffs'] = pd
    for i, k, ov, cv in pd:
        if k in ('offset', 'vaddr', 'paddr'):
            (A if ov - cv == text_gap else B).append(f'phdr[{i}].{k} shift {ov - cv}')
        elif k in ('filesz', 'memsz'):
            if i == 0: (A if ov - cv == body_delta else B).append(f'phdr[0].{k} gap {ov - cv} = body delta')
            elif i == 2: (A if ov - cv == rel_gap else B).append(f'phdr[2].{k} gap {ov - cv} = rel.dyn gap')
            else: B.append(f'phdr[{i}].{k} {ov} vs {cv}')
        else: B.append(f'phdr[{i}].{k} {ov} vs {cv}')
    # ---- identical-content sections
    for n in ('.rodata', '.dynstr', '.shstrtab'):
        eq = O['data'](n) == C['data'](n)
        rep[n + '_equal'] = eq
        if not eq: B.append(f'{n} content differs')
    # ---- .text: matched windows under translation
    orel = {off: (t, s) for off, t, s in O['rel']}; crel = {off: (t, s) for off, t, s in C['rel']}
    odyn, cdyn = O['dynsym'], C['dynsym']
    text_bad = []; text_checked = 0; call_fix = lddw_fix = 0; raw_equal = 0
    for i in range(min(len(ow), len(cw))):
        o, c = ow[i], cw[i]
        if o['signature'] != c['signature']: continue
        text_checked += 1
        ob = m.at_address(oimg, o['address'], o['bytes']); cb = bytearray(m.at_address(cimg, c['address'], c['bytes']))
        if ob == bytes(cb): raw_equal += 1
        p = 0
        while p < len(cb):
            op = cb[p]; width = 16 if op == 0x18 else 8
            ca = c['address'] + p; oa = o['address'] + p
            if op == 0x85 and (cb[p + 1] >> 4) == 1 and crel.get(ca, (0,))[0] != 10:
                imm = struct.unpack_from('<i', cb, p + 4)[0]; tgt = ca + 8 + imm * 8
                mt = M(tgt)
                if mt is None: text_bad.append((o['address'], p, 'call target untranslatable', tgt)); p += width; continue
                struct.pack_into('<i', cb, p + 4, (mt - (oa + 8)) // 8); call_fix += 1
            elif op == 0x18 and crel.get(ca, (0,))[0] == 8:
                v = int.from_bytes(cb[p + 4:p + 8] + cb[p + 12:p + 16], 'little'); mv = M(v)
                if mv is None: text_bad.append((o['address'], p, 'lddw target untranslatable', v)); p += width; continue
                cb[p + 4:p + 8] = (mv & 0xffffffff).to_bytes(4, 'little'); cb[p + 12:p + 16] = (mv >> 32).to_bytes(4, 'little'); lddw_fix += 1
            p += width
        if bytes(cb) != ob:
            diffs = [q for q in range(0, len(ob), 8) if ob[q:q + 8] != bytes(cb[q:q + 8])]
            text_bad.append((o['address'], 'bytes differ after translation', diffs[:8], len(diffs)))
    rep['text'] = dict(matched_windows_checked=text_checked, raw_equal_in_place=raw_equal,
                       translated_calls=call_fix, translated_lddw=lddw_fix, residual=text_bad[:40], residual_count=len(text_bad))
    if text_bad: B.append(f'.text: {len(text_bad)} matched-window residuals after address translation')
    else: A.append(f'.text: all {text_checked} matched windows byte-equal after translating {call_fix} call displacements and {lddw_fix} lddw addresses')
    # ---- unmatched bodies: relocation and target inventory
    def body_inv(img, P, addr, size):
        rel = {off: (t, s) for off, t, s in P['rel']}
        rows = m.instructions(img, addr, size); calls = []; imports = []; lddw = []
        for r in rows:
            a_ = addr + r['offset']; t = rel.get(a_)
            if t and t[0] == 10: imports.append(P['dynsym'][t[1]]['name'])
            elif 'call_target' in r: calls.append(r['call_target'])
            if t and t[0] == 8: lddw.append(r.get('lddw_value'))
        return dict(instructions=len(rows), calls=len(calls), imports=collections.Counter(imports),
                    lddw_relocs=len(lddw), call_targets=calls, lddw_targets=lddw)
    um = []
    for i, o, c in unmatched:
        bo = body_inv(oimg, O, o['address'], o['bytes']); bc = body_inv(cimg, C, c['address'], c['bytes'])
        # translate candidate targets
        ct = collections.Counter(M(t) for t in bc['call_targets']); ot = collections.Counter(bo['call_targets'])
        cl = collections.Counter(M(t) for t in bc['lddw_targets']); ol = collections.Counter(bo['lddw_targets'])
        um.append(dict(orig_addr=o['address'], name=names.get(c['address']),
            orig=dict(instructions=bo['instructions'], calls=bo['calls'], lddw_relocs=bo['lddw_relocs'], imports=dict(bo['imports'])),
            cand=dict(instructions=bc['instructions'], calls=bc['calls'], lddw_relocs=bc['lddw_relocs'], imports=dict(bc['imports'])),
            callee_multiset_equal=ct == ot, callees_only_orig=sorted((ot - ct).elements()), callees_only_cand=sorted(x for x in (ct - ot).elements() if x is not None),
            data_multiset_equal=cl == ol, data_only_orig=sorted((ol - cl).elements()), data_only_cand=sorted(x for x in (cl - ol).elements() if x is not None)))
    for x in extra:
        bx = body_inv(cimg, C, x['address'], x['bytes'])
        um.append(dict(extra_cand_addr=x['address'], name=names.get(x['address']),
                       cand=dict(instructions=bx['instructions'], calls=bx['calls'], lddw_relocs=bx['lddw_relocs'], imports=dict(bx['imports'])),
                       callees=sorted(M(t) for t in bx['call_targets'] if M(t) is not None), data=sorted(M(t) for t in bx['lddw_targets'] if M(t) is not None)))
    rep['unmatched_bodies'] = um
    # ---- .rel.dyn under translation
    in_unmatched_o = lambda off: any(o['address'] <= off < o['address'] + o['bytes'] for _, o, _ in unmatched)
    in_unmatched_c = lambda off: any(c['address'] <= off < c['address'] + c['bytes'] for _, _, c in unmatched) or \
                                 any(x['address'] <= off < x['address'] + x['bytes'] for x in extra)
    def sym_name(P, idx): return P['dynsym'][idx]['name'] if idx else ''
    orl = [(off, t, sym_name(O, s)) for off, t, s in O['rel'] if not in_unmatched_o(off)]
    crl = [(M(off), t, sym_name(C, s)) for off, t, s in C['rel'] if not in_unmatched_c(off)]
    ou = collections.Counter((t, sym_name(O, s)) for off, t, s in O['rel'] if in_unmatched_o(off))
    cu = collections.Counter((t, sym_name(C, s)) for off, t, s in C['rel'] if in_unmatched_c(off))
    rel_set_equal = collections.Counter(orl) == collections.Counter(crl)
    rel_order_equal = orl == crl
    rep['rel_dyn'] = dict(original_entries=len(O['rel']), candidate_entries=len(C['rel']),
        outside_unmatched_original=len(orl), outside_unmatched_candidate=len(crl),
        outside_multiset_equal=rel_set_equal, outside_order_equal=rel_order_equal,
        inside_unmatched_original={f'{k[0]}:{k[1]}': v for k, v in ou.items()},
        inside_unmatched_candidate={f'{k[0]}:{k[1]}': v for k, v in cu.items()},
        original_sorted=[x[0] for x in O['rel'] if x[1] == 8] == sorted(x[0] for x in O['rel'] if x[1] == 8),
        type_order_original=[k for k, _ in __import__('itertools').groupby(t for _, t, _ in O['rel'])],
        type_order_candidate=[k for k, _ in __import__('itertools').groupby(t for _, t, _ in C['rel'])])
    if rel_set_equal and rel_order_equal:
        A.append(f'.rel.dyn: {len(orl)} entries outside unmatched bodies equal in content and order after translation; '
                 f'inside unmatched: orig {dict(ou)} vs cand {dict(cu)}')
    else:
        B.append('.rel.dyn entries outside unmatched bodies differ after translation')
    # ---- .data.rel.ro under translation
    od, cd = bytearray(O['data']('.data.rel.ro')), bytearray(C['data']('.data.rel.ro'))
    obase, cbase = O['secs']['.data.rel.ro']['addr'], C['secs']['.data.rel.ro']['addr']
    dbad = []; dfix = 0
    for off, t, s in C['rel']:
        if t == 8 and cbase <= off < cbase + len(cd):
            q = off - cbase; lo, hi = struct.unpack_from('<II', cd, q); mv = M(hi)
            if mv is None: dbad.append((q, 'untranslatable', hi)); continue
            struct.pack_into('<II', cd, q, lo, mv); dfix += 1
    if bytes(cd) != bytes(od):
        diffs = [q for q in range(0, len(od), 8) if od[q:q + 8] != cd[q:q + 8]]
        dbad.append(('fields differ', len(diffs), [(q, od[q:q + 8].hex(), cd[q:q + 8].hex()) for q in diffs[:10]]))
    rep['data_rel_ro'] = dict(bytes=len(od), translated_pointers=dfix, residual=dbad)
    if dbad: B.append(f'.data.rel.ro residual after translating pointers: {dbad[:3]}')
    else: A.append(f'.data.rel.ro: all {len(od)} bytes equal after translating {dfix} relocated pointers')
    # ---- .dynsym
    sbad = []
    for so, sc in zip(odyn, cdyn):
        for k in ('name', 'name_off', 'info', 'other', 'shndx', 'size'):
            if so[k] != sc[k]: sbad.append((so['name'], k, so[k], sc[k]))
        if so['value'] != sc['value']:
            mv = M(sc['value'])
            if mv != so['value']: sbad.append((so['name'], 'value', so['value'], sc['value'], mv))
            else: A.append(f'.dynsym {so["name"]} value {so["value"]:#x} vs {sc["value"]:#x} (translated equal)')
    if len(odyn) != len(cdyn): sbad.append(('count', len(odyn), len(cdyn)))
    rep['dynsym'] = dict(entries=len(odyn), order=[s['name'] for s in odyn], residual=sbad)
    if sbad: B.append(f'.dynsym residual {sbad}')
    # ---- .dynamic
    dbad2 = []
    nrel_o = len(O['rel']); nrel_c = len(C['rel'])
    rc_o = sum(1 for x in O['rel'] if x[1] == 8); rc_c = sum(1 for x in C['rel'] if x[1] == 8)
    for (to, vo), (tc, vc) in zip(O['dynamic'], C['dynamic']):
        if to != tc: dbad2.append(('tag', to, tc)); continue
        if vo == vc: continue
        nm = DT.get(to, hex(to))
        if nm in ('REL', 'SYMTAB', 'STRTAB'):
            (A if M(vc) == vo else B).append(f'.dynamic {nm} {vo:#x} vs {vc:#x} (translated)')
        elif nm == 'RELSZ':
            (A if (vo - vc) == (nrel_o - nrel_c) * 16 else B).append(f'.dynamic RELSZ {vo} vs {vc} = entry count gap')
        elif nm == 'RELCOUNT':
            (A if (vo, vc) == (rc_o, rc_c) else B).append(f'.dynamic RELCOUNT {vo} vs {vc} = relative-reloc count gap (in unmatched bodies)')
        else:
            dbad2.append((nm, vo, vc))
    rep['dynamic'] = dict(entries=[(DT.get(t, hex(t)), v) for t, v in O['dynamic']], residual=dbad2)
    if dbad2: B.append(f'.dynamic residual {dbad2}')
    # ---- gaps / padding between sections (file layout)
    def gaps(P, img):
        out = []; secs = sorted([s for s in P['sections'] if s['type'] != 0], key=lambda s: s['offset'])
        pos = P['header']['phoff'] + P['header']['phnum'] * P['header']['phentsize']
        for s in secs:
            if s['offset'] > pos: out.append((s['name'], s['offset'] - pos, img[pos:s['offset']].hex() if s['offset'] - pos <= 16 else 'len>16'))
            pos = max(pos, s['offset'] + (s['size'] if s['type'] != 8 else 0))
        if P['header']['shoff'] > pos: out.append(('shdrs', P['header']['shoff'] - pos, img[pos:P['header']['shoff']].hex()))
        return out
    rep['gaps'] = dict(original=gaps(O, oimg), candidate=gaps(C, cimg))
    if [(n, l, h) for n, l, h in rep['gaps']['original']] != [(n, l, h) for n, l, h in rep['gaps']['candidate']]:
        B.append(f'inter-section padding differs: {rep["gaps"]}')
    else: A.append(f'inter-section padding identical: {rep["gaps"]["original"]}')
    rep['A_consequences'] = A; rep['B_independent'] = B
    if a.json: Path(a.json).write_text(json.dumps(rep, indent=1, default=str) + '\n')
    if not a.quiet:
        print(json.dumps({k: rep[k] for k in ('original', 'candidate', 'windows')}, indent=1, default=str))
        print('\n(a) CONSEQUENCES of unmatched bodies:'); [print('  -', x) for x in A]
        print('\n(b) INDEPENDENT residuals:'); [print('  -', x) for x in B] if B else print('  (none)')
        print('\nunmatched body inventory:')
        for u in um: print('  ', json.dumps(u, default=str)[:900])
    return 0 if not B else 1

if __name__ == '__main__':
    sys.exit(main())
