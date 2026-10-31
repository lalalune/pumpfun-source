#!/usr/bin/env python3
"""cls.py <fn.bin|unstripped.so> lo hi [--show]: classify the masked-structure (sk) misses of an orig region of
admin_cto::execute (0x22a10). The candidate range is found by call landmarks (same call index before lo / at hi).
Levels as w14a38 splice.py: L1 masks r10 displacements and negative add64 imms, L2 also registers, L3 also jump offsets.
Each unmatched orig (del) / cand (ins) instruction at L3 gets a category."""
import sys, struct, difflib, re, json, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rx_lib as R
def insns(raw):
    out = []; i = 0
    while i < len(raw):
        n = 16 if raw[i] == 0x18 else 8; out.append((i, raw[i:i+n])); i += n
    return out
def mask(t, lvl):
    b = bytearray(t); op = b[0]
    if op == 0x85: b[1] &= 0x0f; b[4:8] = b'\0'*4
    if op == 0x18: b[4:8] = b'\0'*4; b[12:16] = b'\0'*4
    if lvl == 0: return bytes(b)
    dst = b[1] & 15; src = b[1] >> 4; cls = op & 7
    if cls in (1, 2, 3) and (dst == 10 or src == 10): b[2:4] = b'\0\0'
    if op == 0x07 and struct.unpack_from('<i', b, 4)[0] < 0: b[4:8] = b'\0'*4
    if lvl >= 2: b[1] = 0
    if lvl >= 3 and cls in (5, 6) and op not in (0x85, 0x95, 0x8d): b[2:4] = b'\0\0'
    return bytes(b)
SZ = {0x71: 'b', 0x69: 'h', 0x61: 'w', 0x79: 'dw', 0x73: 'b', 0x6b: 'h', 0x63: 'w', 0x7b: 'dw', 0x72: 'b', 0x6a: 'h', 0x62: 'w', 0x7a: 'dw'}
def cat(t):
    op = t[0]; dst = t[1] & 15; src = t[1] >> 4; off = struct.unpack_from('<h', t, 2)[0]; imm = struct.unpack_from('<i', t, 4)[0]
    cls = op & 7
    if op == 0x85: return 'call'
    if op == 0x18: return 'lddw'
    if cls == 1:  # ldx
        if src == 10: return 'frame-load'
        if off in (40, 41, 42): return 'ai-flag-load'
        if off in (24, 32): return 'ai-owner/rent-load'
        if off in (0, 8, 16): return 'ptr-load+%d' % off
        return 'acc-field-load'
    if cls == 3:  # stx
        if dst == 10: return 'frame-store-' + SZ.get(op, '?')
        return 'mem-store'
    if cls == 2: return 'frame-store-imm' if dst == 10 else 'mem-store-imm'
    if cls in (5, 6): return 'jump'
    if op in (0xbf,): return 'mov-reg' if src != 10 else 'frame-addr'
    if op in (0xb7, 0xb4): return 'mov-imm'
    if op == 0x07: return 'add-imm'
    return 'alu'
def calls(ins): return [o for o, t in ins if t[0] == 0x85]
def main():
    a = sys.argv[1:]; src = a[0]; lo = int(a[1], 0); hi = int(a[2], 0); show = '--show' in a
    lvl = int(a[a.index('--lvl')+1]) if '--lvl' in a else 3
    orig = R.orig_window(); cand = R.cand_fn(src)
    O = insns(orig); C = insns(cand); oc = calls(O); cc = calls(C)
    def cidx(off): return sum(1 for x in oc if x < off)
    i_lo, i_hi = cidx(lo), cidx(hi)
    # candidate bounds: same number of preceding calls; offset within segment by instruction count from the call
    def cmap(off, k):
        base_o = oc[k-1] if k else -8; base_c = cc[k-1] if k else -8
        n = len([1 for o, _ in O if base_o < o < off]); seg = [o for o, _ in C if o > base_c]
        return seg[n] if n < len(seg) else len(cand)
    clo, chi = cmap(lo, i_lo), cmap(hi, i_hi)
    if hi in oc: chi = cc[oc.index(hi)]  # hi on a call: exact landmark
    Or = [(o, t) for o, t in O if lo <= o < hi]; Cr = [(o, t) for o, t in C if clo <= o < chi]
    res = {'lo': hex(lo), 'hi': hex(hi), 'clo': hex(clo), 'chi': hex(chi), 'n_orig': len(Or), 'n_cand': len(Cr)}
    miss = []
    for L in range(4):
        sm = difflib.SequenceMatcher(None, [mask(t, L) for _, t in Or], [mask(t, L) for _, t in Cr], autojunk=False)
        miss.append(len(Or) - sum(x.size for x in sm.get_matching_blocks()))
    for L in range(1, 4): miss[L] = min(miss[L], miss[L-1])
    res.update(miss=miss[0], fm=miss[0]-miss[1], rm=miss[1]-miss[2], jm=miss[2]-miss[3], sk=miss[3])
    sm = difflib.SequenceMatcher(None, [mask(t, lvl) for _, t in Or], [mask(t, lvl) for _, t in Cr], autojunk=False)
    dc = collections.Counter(); ic = collections.Counter()
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal': continue
        for o, t in Or[i1:i2]: dc[cat(t)] += 1
        for o, t in Cr[j1:j2]: ic[cat(t)] += 1
        if show:
            print('--- %s o%04x[%d] c%04x[%d]' % (tag, Or[i1][0] if i1 < len(Or) else hi, i2-i1, Cr[j1][0] if j1 < len(Cr) else chi, j2-j1))
            for x in range(max(i2-i1, j2-j1)):
                ol = R.dis(*Or[i1+x]) if i1+x < i2 else ''; cl = R.dis(*Cr[j1+x]) if j1+x < j2 else ''
                print('   %-40s | %s' % (ol, cl))
    res['del'] = dict(dc.most_common()); res['ins'] = dict(ic.most_common())
    print(json.dumps(res))
main()
