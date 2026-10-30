#!/usr/bin/env python3
"""Extract Anchor/Rust Source coordinates embedded as code immediates.

Source {filename: &str, line: u32} on the stack: ptr @X-8 (stxdw from an lddw'd reg), len @X
(stdw imm), line @X+8 (stw imm). The pointer is resolved to the actual path string bytes.

  coords.py window <orig_start>             # sites in one original window
  coords.py fn <cand_addr> [--cand so]      # sites in one candidate function
  coords.py unmatched [--cand so]           # unmatched windows: original sites vs coordinate-only equal-length candidate
"""
import argparse, hashlib, json, struct, sys
from pathlib import Path

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
from score import sections, body, original_windows, score_with_hash, BASE, normalize  # noqa
from score_admission import report_destination
from elf_symbols import function_symbols


def read_cstr_at(blob, secs, vaddr, length):
    if length < 0:
        return None
    for name, s in secs.items():
        if s['addr'] and s['addr'] <= vaddr < s['addr'] + s['size']:
            o = vaddr - s['addr'] + s['offset']
            if vaddr + length > s['addr'] + s['size'] or not 0 <= o <= len(blob) - length:
                return None
            return blob[o:o + length]
    return None


def sites(blob, secs, start, raw):
    out = []
    n = len(raw); i = 0; insn = []
    while i < n:
        op = raw[i]
        if op == 0x18:
            lo = struct.unpack_from('<I', raw, i + 4)[0]; hi = struct.unpack_from('<I', raw, i + 12)[0]
            insn.append((i, op, raw[i + 1], 0, lo | hi << 32)); i += 16
        else:
            _, regs, off, imm = struct.unpack_from('<BBhi', raw, i)
            insn.append((i, op, regs, off, imm)); i += 8
    dst = lambda regs: regs & 0xf
    src = lambda regs: regs >> 4
    for k, (pos, op, regs, off, L) in enumerate(insn):
        if not (op == 0x7a and dst(regs) == 10 and 1 <= L <= 200):
            continue
        X = off
        lo, hi = max(0, k - 30), min(len(insn), k + 30)
        # Stack slots are reused by nearby Source descriptors. Pair with the
        # nearest matching store, preferring a preceding store on a tie.
        nearby = sorted(range(lo, hi), key=lambda j: (abs(j - k), j > k))
        ptr = None
        for j in nearby:
            p2, o2, r2, of2, v2 = insn[j]
            if o2 == 0x7b and dst(r2) == 10 and of2 == X - 8:
                ry = src(r2)
                for jj in range(j - 1, max(-1, j - 40), -1):
                    p3, o3, r3, of3, v3 = insn[jj]
                    if o3 in (0x85, 0x8d) and ry <= 5:
                        break  # Calls may overwrite caller-saved pointer registers.
                    if dst(r3) == ry and o3 == 0x18:
                        ptr = v3; break
                    if dst(r3) == ry and o3 not in (0x7b, 0x7a, 0x62, 0x72, 0x6a, 0x63, 0x73, 0x6b):
                        break
                if ptr is not None:
                    break
        if ptr is None:
            continue
        s = read_cstr_at(blob, secs, ptr, L)
        if not (s and s.endswith(b'.rs') and all(32 <= c < 127 for c in s)):
            continue
        line = None; line_slot = None
        for j in nearby:
            p2, o2, r2, of2, v2 = insn[j]
            if o2 == 0x62 and dst(r2) == 10 and of2 == X + 8:
                line, line_slot = v2, p2; break
        out.append({'slot': pos, 'path': s.decode(), 'line': line, 'len_slot': pos, 'line_slot': line_slot})
    return out


from original_input import resolve_original
ORIG = resolve_original(BASE / 'original.so').read_bytes(); OS = sections(ORIG)


def orig_sites(start):
    w = next(x for x in original_windows() if x['start'] == start)
    return sites(ORIG, OS, start, w['raw'])


def cand_sites(cand_blob, cs, addr, size):
    return sites(cand_blob, cs, addr, body(cand_blob, cs, addr, size))


def non_coordinate_slots(original, candidate, source_sites):
    """Return differing normalized slots outside Source coordinate fields."""
    if len(original) != len(candidate):
        raise ValueError('coordinate classification requires equal-length bodies')
    coordinate_slots = {s[key]: opcode for s in source_sites
                        for key, opcode in [('len_slot', 0x7a), ('line_slot', 0x62)]
                        if s[key] is not None}
    return [i for i in range(0, len(original), 8)
            if original[i:i + 8] != candidate[i:i + 8]
            and not (coordinate_slots.get(i) == original[i]
                     and original[i:i + 4] == candidate[i:i + 4])]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('window'); p.add_argument('start')
    p = sub.add_parser('fn'); p.add_argument('addr'); p.add_argument('--cand', type=Path, default=BASE / 'current/unstripped.so')
    p = sub.add_parser('unmatched'); p.add_argument('--cand', type=Path, default=BASE / 'current/unstripped.so'); p.add_argument('--json', type=Path)
    a = ap.parse_args()
    if a.cmd == 'window':
        print(json.dumps(orig_sites(int(a.start, 0)), indent=1))
    elif a.cmd == 'fn':
        blob = a.cand.read_bytes(); cs = sections(blob)
        f = next((s, n, nm) for (s, n, nm) in function_symbols(blob) if s == int(a.addr, 0))
        print(json.dumps(cand_sites(blob, cs, f[0], f[1]), indent=1))
    else:
        if a.json:
            try:
                report_destination(a.json, [a.cand])
            except ValueError as error:
                ap.error(str(error))
        blob = a.cand.read_bytes(); cs = sections(blob)
        cur, candidate_hash = score_with_hash(a.cand)
        if candidate_hash != hashlib.sha256(blob).hexdigest():
            ap.error('candidate changed during coordinate analysis; retry with a stable file')
        bylen = {}
        for s, n, nm in function_symbols(blob):
            bylen.setdefault(n, []).append((s, nm))
        rows = []
        for w in original_windows():
            if cur[w['start']]['normalized']:
                continue
            osites = sites(ORIG, OS, w['start'], w['raw'])
            if not osites:
                continue
            best = None
            on = normalize(w['raw'], w['start'], OS)
            for (s, nm) in bylen.get(w['bytes'], []):
                cn = normalize(body(blob, cs, s, w['bytes']), s, cs)
                diff = [i for i in range(0, len(on), 8) if on[i:i + 8] != cn[i:i + 8]]
                if diff and not non_coordinate_slots(on, cn, osites):
                    best = (s, nm, diff, cand_sites(blob, cs, s, w['bytes'])); break
            rows.append({'start': hex(w['start']), 'bytes': w['bytes'], 'original_sites': osites,
                         'coordinate_only_candidate': None if not best else {'addr': hex(best[0]), 'symbol': best[1], 'diff_slots': best[2], 'candidate_sites': best[3]}})
        if a.json:
            a.json.write_text(json.dumps(rows, indent=1))
        co = [r for r in rows if r['coordinate_only_candidate']]
        print(f"unmatched windows with Source sites: {len(rows)}; coordinate-only vs an equal-length candidate: {len(co)} ({sum(r['bytes'] for r in co)} B)")


if __name__ == '__main__':
    main()
