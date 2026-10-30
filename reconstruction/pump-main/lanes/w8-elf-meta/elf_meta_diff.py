#!/usr/bin/env python3
"""Whole meaningful-ELF comparison of a stripped candidate with the captured original, split by cause.

Meaningful ELF = original[:e_shoff + e_shnum*e_shentsize] (the ProgramData zero tail is excluded),
the same boundary the Mayhem/Fees verifiers use. Every non-.text difference is classified as either
  - a build-input effect (section/segment/symbol/dynamic structure, flags, alignment, SBPF e_flags,
    stripping, string tables), which a recipe change could fix, or
  - a consequence of .text content: the .text size delta D shifts every later address, extra/missing
    text relocations change .rel.dyn/RELSZ/RELCOUNT/e_shoff, and .rodata/.data.rel.ro bytes that are
    permutations or pointers.
Diagnostic only: it reads the two ELFs and prints JSON; it never writes or rewrites an ELF.

usage: elf_meta_diff.py ORIGINAL CANDIDATE_STRIPPED [--unstripped U] [--json OUT]
"""
import argparse, collections, json, struct as S, sys

def parse(b):
    eh = dict(zip('ident type machine version entry phoff shoff flags ehsize phentsize phnum shentsize shnum shstrndx'.split(),
                  S.unpack_from('<16sHHIQQQIHHHHHH', b, 0)))
    phs = [dict(zip('type flags offset vaddr paddr filesz memsz align'.split(), S.unpack_from('<IIQQQQQQ', b, eh['phoff'] + 56 * i)))
           for i in range(eh['phnum'])]
    raw = [S.unpack_from('<IIQQQQIIQQ', b, eh['shoff'] + 64 * i) for i in range(eh['shnum'])]
    so = raw[eh['shstrndx']][4]
    name = lambda o: b[so + o:b.index(b'\0', so + o)].decode()
    secs = collections.OrderedDict()
    for r in raw:
        secs[name(r[0])] = dict(zip('name type flags addr offset size link info align entsize'.split(), r))
    return eh, phs, secs

def data(b, s): return b[s['offset']:s['offset'] + s['size']]

def rels(b, secs):
    r = data(b, secs['.rel.dyn']); return [S.unpack_from('<QQ', r, i) for i in range(0, len(r), 16)]

def dynsyms(b, secs):
    st, sstr = data(b, secs['.dynsym']), data(b, secs['.dynstr'])
    out = []
    for i in range(0, len(st), 24):
        n, info, oth, shn, val, sz = S.unpack_from('<IBBHQQ', st, i)
        out.append((sstr[n:sstr.index(b'\0', n)].decode(), info, oth, shn, val, sz))
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('original'); ap.add_argument('candidate')
    ap.add_argument('--unstripped'); ap.add_argument('--json')
    a = ap.parse_args()
    o, c = open(a.original, 'rb').read(), open(a.candidate, 'rb').read()
    oeh, oph, os_ = parse(o); ceh, cph, cs = parse(c)
    ext = oeh['shoff'] + oeh['shnum'] * oeh['shentsize']
    rep = {'original_meaningful_bytes': ext, 'original_tail_all_zero': not any(o[ext:]),
           'candidate_bytes': len(c), 'meaningful_elf_equal': c == o[:ext]}
    D = cs['.text']['size'] - os_['.text']['size']
    ro, rc = rels(o, os_), rels(c, cs)
    R = 16 * (len(rc) - len(ro))
    rep['text_size_delta'] = D; rep['rel_dyn_entry_delta'] = len(rc) - len(ro)
    build_input = []      # differences a recipe/build-input change would have to explain
    explained = []        # differences fully implied by .text content
    def note(ok, what, detail):
        (explained if ok else build_input).append({'what': what, 'detail': detail})
    # ELF header
    for k in oeh:
        if oeh[k] == ceh[k]: continue
        if k == 'entry': note(ceh[k] - D == oeh[k], 'e_entry', [hex(oeh[k]), hex(ceh[k])])
        elif k == 'shoff': note(ceh[k] - D - R == oeh[k], 'e_shoff', [hex(oeh[k]), hex(ceh[k])])
        else: note(False, 'ehdr.' + k, [oeh[k], ceh[k]])
    rep['e_flags'] = [oeh['flags'], ceh['flags']]
    # sections
    if list(os_) != list(cs): note(False, 'section names/order', [list(os_), list(cs)])
    textend = os_['.text']['addr'] + os_['.text']['size']
    for n in os_:
        if n not in cs: continue
        x, y = os_[n], cs[n]
        for k in x:
            if x[k] == y[k]: continue
            if k in ('addr', 'offset') and x[k] >= textend and n != '.shstrtab': ok = y[k] - D == x[k]
            elif k == 'offset' and n == '.shstrtab': ok = y[k] - D - R == x[k]
            elif k == 'size' and n == '.text': ok = True
            elif k == 'size' and n == '.rel.dyn': ok = y[k] - R == x[k]
            else: ok = False
            note(ok, f'{n}.{k}', [x[k], y[k]])
    # program headers
    if len(oph) != len(cph): note(False, 'phnum', [len(oph), len(cph)])
    for i, (x, y) in enumerate(zip(oph, cph)):
        for k in x:
            if x[k] == y[k]: continue
            if k in ('offset', 'vaddr', 'paddr'): ok = x[k] >= textend and y[k] - D == x[k]
            elif k in ('filesz', 'memsz'): ok = y[k] - x[k] in (D, R)
            else: ok = False
            note(ok, f'phdr{i}.{k}', [hex(x[k]), hex(y[k])])
    # string tables and symbols
    for n in ('.dynstr', '.shstrtab'):
        note(data(o, os_[n]) == data(c, cs[n]), n + ' bytes', 'equal' if data(o, os_[n]) == data(c, cs[n]) else 'differ')
    od, cd = dynsyms(o, os_), dynsyms(c, cs)
    if [s[:4] + s[5:] for s in od] != [s[:4] + s[5:] for s in cd]: note(False, '.dynsym names/order/info/size', 'differ')
    for x, y in zip(od, cd):
        if x[4] != y[4]: note(y[4] - D == x[4], f'.dynsym value {x[0]}', [hex(x[4]), hex(y[4])])
    # .dynamic
    def dyn(b, s):
        d = data(b, s['.dynamic']); return [S.unpack_from('<qQ', d, i) for i in range(0, len(d), 16)]
    for (t1, v1), (t2, v2) in zip(dyn(o, os_), dyn(c, cs)):
        if t1 != t2: note(False, '.dynamic tag order', [t1, t2])
        elif v1 != v2:
            ok = {0x11: v2 - D == v1, 6: v2 - D == v1, 5: v2 - D == v1, 0x12: v2 - R == v1, 0x6ffffffa: True}.get(t1, False)
            note(ok, f'.dynamic tag {t1:#x}', [v1, v2])
    # relocations by (place, type, symbol)
    def cls(rs, secs):
        t = secs['.text']; return collections.Counter(('text' if t['addr'] <= off < t['addr'] + t['size'] else 'data', i & 0xffffffff, i >> 32) for off, i in rs)
    co, cc = cls(ro, os_), cls(rc, cs)
    rep['reloc_class_deltas'] = {f'{k[0]}:type{k[1]}:sym{k[2]}': cc[k] - co[k] for k in set(co) | set(cc) if cc[k] != co[k]}
    note(all(k[0] == 'text' for k in co ^ cc if co[k] != cc[k]) if False else all(k[0] == 'text' for k in set(co) | set(cc) if co[k] != cc[k]),
         'relocation multiset', rep['reloc_class_deltas'])
    # .rodata: same size, differing runs, and whether the difference is a permutation
    A, B = data(o, os_['.rodata']), data(c, cs['.rodata'])
    runs, i = [], 0
    while i < min(len(A), len(B)):
        if A[i] != B[i]:
            j = i
            while j < len(A) and A[j] != B[j]: j += 1
            runs.append([i, j]); i = j
        else: i += 1
    if runs:
        lo, hi = runs[0][0], runs[-1][1]
        perm = len(A) == len(B) and sorted(A[lo:hi]) == sorted(B[lo:hi])
        rep['rodata_diff_span'] = {'offset': lo, 'orig_vaddr': hex(os_['.rodata']['addr'] + lo), 'bytes': hi - lo,
                                   'orig': A[lo:hi].decode('latin1'), 'cand': B[lo:hi].decode('latin1'), 'byte_permutation': perm}
        explained.append({'what': '.rodata order', 'detail': 'string allocation order (source/codegen order), not a build-input; same size' if perm else 'content differs'})
    # .data.rel.ro: non-pointer bytes
    def dptr(rs, secs):
        d = secs['.data.rel.ro']; return {off - d['addr'] for off, i in rs if d['addr'] <= off < d['addr'] + d['size']}
    po, pc = dptr(ro, os_), dptr(rc, cs)
    A, B = data(o, os_['.data.rel.ro']), data(c, cs['.data.rel.ro'])
    mask = set(k + j for k in po for j in range(8))
    nonptr = [k for k in range(len(A)) if k not in mask and A[k] != B[k]]
    note(po == pc and not nonptr, '.data.rel.ro', {'pointer_slots_equal': po == pc, 'nonpointer_bytes_differing': len(nonptr)})
    if a.unstripped:
        u = open(a.unstripped, 'rb').read(); _, _, us = parse(u)
        st, sstr = data(u, us['.symtab']), data(u, us['.strtab'])
        fns = {}
        for i in range(0, len(st), 24):
            n, info, oth, shn, val, sz = S.unpack_from('<IBBHQQ', st, i)
            if info & 0xf == 2 and sz: fns.setdefault(val, (sz, sstr[n:sstr.index(b'\0', n)].decode()))
        rep['candidate_functions'] = len(fns)
        rep['candidate_function_bytes'] = sum(v[0] for v in fns.values())
    rep['build_input_differences'] = build_input
    rep['text_content_differences'] = explained
    rep['verdict'] = ('meaningful ELF identical' if rep['meaningful_elf_equal'] else
                      'all non-.text differences follow from .text content' if not build_input else
                      'build-input-controlled differences remain')
    s = json.dumps(rep, indent=1)
    if a.json: open(a.json, 'w').write(s + '\n')
    print(s)
    return 0 if not build_input else 1

if __name__ == '__main__':
    sys.exit(main())
