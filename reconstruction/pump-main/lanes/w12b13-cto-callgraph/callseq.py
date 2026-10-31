#!/usr/bin/env python3
"""Call-sequence alignment: original window vs candidate function.

  callseq.py [--cand unstripped.so] [--window 0x22a10] [--sym REGEX] [--table] [--json out.json]

Lists every call instruction (internal pc-relative calls and syscalls named
through .rel.dyn) in layout order for the original window and the candidate
function, names internal targets with the candidate's symbol table (an address-based label from a same-layout build is an analysis aid, not proof
of original source identity), and aligns the two
sequences with difflib. Each non-equal opcode is a statement-order, inlining or
helper-boundary difference.
"""
import argparse, difflib, json, struct, sys
from pathlib import Path

HERE = Path(__file__).resolve()
HARNESS = HERE.parents[3] / 'harness'
sys.path.insert(0, str(HARNESS))
from score import body, sections, BASE  # noqa: E402
from original_input import resolve_original  # noqa: E402
from elf_symbols import function_symbols  # noqa: E402
from win import demangle  # noqa: E402

DEFAULT_CAND = Path.home() / '.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so'


def shdrs(blob):
    shoff = struct.unpack_from('<Q', blob, 40)[0]
    esz, cnt, stri = struct.unpack_from('<HHH', blob, 58)
    hs = [struct.unpack_from('<IIQQQQIIQQ', blob, shoff + i * esz) for i in range(cnt)]
    names = blob[hs[stri][4]:hs[stri][4] + hs[stri][5]]
    def nm(o):
        return names[o:names.index(b'\0', o)].decode()
    return {nm(h[0]): h for h in hs}, hs


def syscall_relocs(blob):
    """Map instruction address -> syscall name from R_BPF_64_32 relocations."""
    by, hs = shdrs(blob)
    out = {}
    rel = by.get('.rel.dyn')
    if not rel:
        return out
    dynsym = hs[rel[6]]
    dynstr = hs[dynsym[6]]
    strs = blob[dynstr[4]:dynstr[4] + dynstr[5]]
    data = blob[rel[4]:rel[4] + rel[5]]
    for o in range(0, len(data), 16):
        off, info = struct.unpack_from('<QQ', data, o)
        typ, sym = info & 0xffffffff, info >> 32
        if typ != 10 or not sym:
            continue
        so = dynsym[4] + sym * 24
        name_off = struct.unpack_from('<I', blob, so)[0]
        out[off] = strs[name_off:strs.index(b'\0', name_off)].decode()
    return out


def body_at(blob, secs, addr, size):
    if size <= 0 or size % 8 or (addr - secs['.text']['addr']) % 8:
        raise ValueError(f'function range {addr:#x}+{size:#x} is not whole instructions')
    return body(blob, secs, addr, size)


def pump_errors():
    import re
    src = (HERE.parents[4] / 'programs/pump/src/lib.rs').read_text().splitlines()
    out, idx, on = {}, 0, False
    for line in src:
        if 'pub enum PumpError' in line:
            on = True
            continue
        if not on:
            continue
        s = line.strip()
        if s.startswith('}'):
            break
        m = re.match(r'^([A-Z][A-Za-z0-9]*)\s*(=\s*(\d+))?\s*,', s)
        if m:
            if m.group(3):
                idx = int(m.group(3))
            out[6000 + idx] = m.group(1)
            idx += 1
    return out


ERRS = pump_errors()


def rodata_u32(blob, secs, addr):
    for name in ('.rodata', '.data.rel.ro'):
        v = secs.get(name)
        if v and v['addr'] <= addr < v['addr'] + v['size'] - 3:
            o = addr - v['addr'] + v['offset']
            return struct.unpack_from('<I', blob, o)[0]
    return None


def label_imms(imms):
    codes = [x for x in imms if 6000 <= x < 6200 or 2000 <= x < 2100]
    lines = [x for x in imms if 280 <= x < 800]
    out = []
    for c in codes:
        out.append(f'E{c}' + (f':{ERRS[c]}' if c in ERRS else ''))
    for l in lines:
        out.append(f'L{l}')
    return ' '.join(out)


def calls(raw, start, relocs, names, blob=None, secs=None):
    seq = []
    i = 0
    lddw = {}
    imms = []
    while i < len(raw):
        op, regs, off, imm = struct.unpack_from('<BBhi', raw, i)
        pc = start + i
        dst = regs & 15
        if op == 0x18:
            lddw[dst] = struct.unpack_from('<I', raw, i + 4)[0] | struct.unpack_from('<I', raw, i + 12)[0] << 32
        elif op in (0x62, 0x6a, 0x72, 0x7a, 0xb7, 0xb4):
            imms.append(imm)
            if op in (0xb7, 0xb4):
                lddw.pop(dst, None)
        elif op & 7 in (4, 7) or op & 7 == 1:
            lddw.pop(dst, None)
        if op == 0x85:
            ann = label_imms(imms)
            if blob is not None:
                for r in (2, 1):
                    if r in lddw:
                        v = rodata_u32(blob, secs, lddw[r])
                        if v is not None and v < 200:
                            ann = (ann + ' ' if ann else '') + f'v{6000 + v}' + (f':{ERRS.get(6000 + v, "?")}' if 6000 + v in ERRS else '')
                            break
            imms = []
            lddw = {}
            seq_ann = ann
        else:
            seq_ann = None
        if op == 0x85:
            src = regs >> 4
            if src == 1 and imm != -1:
                tgt = pc + 8 + imm * 8
                seq.append((pc, 'call', tgt, names.get(tgt, f'?{tgt:#x}'), seq_ann))
            else:
                seq.append((pc, 'sys', None, relocs.get(pc, f'sys{imm:#x}'), seq_ann))
        elif op == 0x8d:
            seq.append((pc, 'callx', None, f'callx r{regs & 15}', None))
        i += 16 if op == 0x18 else 8
    return seq


SHORT = [
    (r'^<anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from$', 'From<AnchorError>'),
    (r'^<anchor_lang::error::Error as core::convert::From<solana_program_error::ProgramError>>::from$', 'From<ProgramError>'),
    (r'^<T as alloc::string::ToString>::to_string$', 'to_string'),
    (r'^<pump_recovered::PumpError as core::fmt::Display>::fmt$', 'PumpError::fmt'),
    (r'^<anchor_lang::error::ErrorCode as core::fmt::Display>::fmt$', 'ErrorCode::fmt'),
    (r'^<solana_account_info::AccountInfo as core::clone::Clone>::clone$', 'AccountInfo::clone'),
    (r'^solana_account_info::AccountInfo::', 'AccountInfo::'),
    (r'^solana_sysvar::clock::.*', 'Clock::get'),
    (r'^solana_sysvar::rent::.*', 'Rent::get'),
    (r'^pump_recovered::', ''),
    (r'^<pump_recovered::(.*)>::', r'<\1>::'),
    (r'^<alloc::vec::Vec<T> as alloc::vec::spec_from_iter::SpecFromIter<T,I>>::from_iter$', 'Vec::from_iter'),
]


def short(name, width=70):
    import re
    d = demangle(name)
    for pat, rep in SHORT:
        d2 = re.sub(pat, rep, d)
        if d2 != d:
            d = d2
            break
    return d if len(d) <= width else d[:width - 1] + '~'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cand', default=str(DEFAULT_CAND))
    ap.add_argument('--orig-names', default=str(DEFAULT_CAND),
                    help='same-layout unstripped build used to name original callees (default: landed main)')
    ap.add_argument('--window', default='0x22a10')
    ap.add_argument('--size', default='27400')
    ap.add_argument('--sym', default=r'admin_cto7execute')
    ap.add_argument('--table', action='store_true', help='print the full aligned table')
    ap.add_argument('--by-site', action='store_true', help='align on callee plus error variant (error-site identity)')
    ap.add_argument('--json')
    a = ap.parse_args()
    if a.json and (Path(a.json).exists() or Path(a.json).is_symlink()):
        ap.error('report already exists; choose a fresh --json path')
    w, wsize = int(a.window, 0), int(a.size, 0)
    orig = resolve_original(BASE / 'original.so').read_bytes()
    osecs = sections(orig)
    try:
        window = body_at(orig, osecs, w, wsize)
    except ValueError as error:
        ap.error(str(error))
    cand = Path(a.cand).read_bytes()
    csecs = sections(cand)
    funcs = function_symbols(cand)
    names = {}
    for s, n, nm in funcs:
        names.setdefault(s, nm)
    # Original callees are named from a same-layout build (every other window is
    # byte-identical there), so candidates of another size still resolve correctly.
    onames = {}
    for s, n, nm in function_symbols(Path(a.orig_names).read_bytes()):
        onames.setdefault(s, nm)
    import re
    cs = [(s, n, nm) for s, n, nm in funcs if re.search(a.sym, nm)]
    if len(cs) != 1:
        sys.exit(f'--sym matched {len(cs)} candidate functions: {[(hex(s), n) for s, n, _ in cs]}')
    cstart, csize, cname = cs[0]
    oseq = calls(window, w, syscall_relocs(orig), onames, orig, osecs)
    cseq = calls(body_at(cand, csecs, cstart, csize), cstart, syscall_relocs(cand), names, cand, csecs)
    import re as _re

    def key(x):
        if not a.by_site:
            return x[3]
        m = _re.search(r'[vE](\d{4})', x[4] or '')
        return x[3] + ('#' + m.group(1) if m else '')
    ok = [key(x) for x in oseq]
    ck = [key(x) for x in cseq]
    sm = difflib.SequenceMatcher(None, ok, ck, autojunk=False)
    print(f'original {w:#x} {wsize} B: {len(oseq)} calls; candidate {cstart:#x} {csize} B: {len(cseq)} calls; '
          f'callee-sequence ratio {sm.ratio():.4f}')
    from collections import Counter
    oc, cc = Counter(x[3] for x in oseq), Counter(x[3] for x in cseq)
    if oc != cc:
        print('multiset differs:')
        for k in sorted(set(oc) | set(cc), key=lambda k: short(k)):
            if oc[k] != cc[k]:
                print(f'  orig {oc[k]} cand {cc[k]}  {short(k)}')
    else:
        print('callee multisets are equal')
    rows = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        for k in range(max(i2 - i1, j2 - j1)):
            o = oseq[i1 + k] if i1 + k < i2 else None
            c = cseq[j1 + k] if j1 + k < j2 else None
            rows.append({'tag': tag,  # noqa
                         'oi': i1 + k if o else None, 'opc': (o[0] - w) if o else None,
                         'ci': j1 + k if c else None, 'cpc': (c[0] - cstart) if c else None,
                         'orig': o[3] if o else None, 'cand': c[3] if c else None,
                         'oann': o[4] if o else None, 'cann': c[4] if c else None})
    if a.table:
        print(f"{'tag':7} {'#o':>4} {'+off':>6} | {'#c':>4} {'+off':>6} | callee (orig / cand)")
        for r in rows:
            o = f"{r['oi']:4d} {r['opc']:#6x}" if r['oi'] is not None else '   -      -'
            c = f"{r['ci']:4d} {r['cpc']:#6x}" if r['ci'] is not None else '   -      -'
            if r['tag'] == 'equal':
                txt = short(r['orig'], 60)
            else:
                txt = f"{short(r['orig'], 40) if r['orig'] else '-'}  //  {short(r['cand'], 40) if r['cand'] else '-'}"
            ann = f"   [{r['oann'] or ''} | {r['cann'] or ''}]" if (r['oann'] or r['cann']) else ''
            print(f"{r['tag'][:7]:7} {o} | {c} | {txt}{ann}")
    else:
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                print(f'equal   o[{i1}:{i2}] c[{j1}:{j2}]  ({i2 - i1} calls) {short(ok[i1], 40)} .. {short(ok[i2 - 1], 40)}')
            else:
                print(f'{tag:7} o[{i1}:{i2}] c[{j1}:{j2}]')
                for k in range(i1, i2):
                    print(f'   - o{k:3d} +{oseq[k][0] - w:#6x} {short(ok[k])}  {oseq[k][4] or ""}')
                for k in range(j1, j2):
                    print(f'   + c{k:3d} +{cseq[k][0] - cstart:#6x} {short(ck[k])}  {cseq[k][4] or ""}')
    if a.json:
        with Path(a.json).open('x', encoding='utf-8') as stream:
            stream.write(json.dumps({'ratio': sm.ratio(), 'orig_calls': len(oseq), 'cand_calls': len(cseq),
                                     'rows': rows}, indent=1) + '\n')


if __name__ == '__main__':
    main()
