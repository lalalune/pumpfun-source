#!/usr/bin/env python3
"""For every normalized-matched window, compare the CONTENT behind each masked lddw pair.

The scorer masks lddw values that point inside an ELF section, so a normalized pair can still
reference different data (a different string, a Location with another line, a vtable for
another type). Those are latent raw/whole-ELF blockers that no text relocation fixes.

For .rodata targets we compare `len` bytes where len is the next immediate length stored or
moved within 4 instructions (string-slice pattern), else 8 bytes. For .data.rel.ro targets we
compare the 24-byte record with pointers resolved (ptr>>32 -> target content prefix).

  lddw_content.py --cand unstripped.so [--json out.json]
"""
import argparse, json, struct, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from linemap import Image, decode, BASE, original_windows, score, candidate_functions, body  # noqa


def sec_of(img, va):
    for n, s in img.secs.items():
        if s['addr'] and s['addr'] <= va < s['addr'] + s['size']:
            return n
    return None


def content(img, va, ln, sec):
    """.data.rel.ro: decode as (ptr<<32, len) slices, compare exactly len bytes behind each ptr.
    .rodata: compare exactly ln bytes (ln from a nearby length immediate), else None (unknown)."""
    if sec == '.data.rel.ro':
        rec = img.read(va, 48) or b''
        out = []; i = 0
        while i + 16 <= len(rec) and len(out) < 2:
            q, n = struct.unpack_from('<QQ', rec, i)
            if q & 0xffffffff == 0 and sec_of(img, q >> 32) and 0 < n < 4096:
                out.append((sec_of(img, q >> 32), img.read(q >> 32, n)))
                i += 16
            else:
                out.append(('val', q)); i += 8
        return tuple(out)
    if ln is None:
        return None
    return img.read(va, ln)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--cand', required=True); ap.add_argument('--json'); a = ap.parse_args()
    orig = Image(BASE / 'original.so'); cand = Image(a.cand)
    cur = score(a.cand)
    addr = {nm: (s, n) for s, n, nm in candidate_functions(a.cand)}
    stats = Counter(); diffs = []
    for w in original_windows():
        r = cur[w['start']]
        if not r['normalized']:
            continue
        best = None
        for nm in r['symbols']:
            s, n = addr[nm]
            oi = decode(w['raw']); ci = decode(body(cand.blob, cand.secs, s, n))
            dd = []
            for k, (o, c) in enumerate(zip(oi, ci)):
                if o[1] != 0x18:
                    continue
                so, sc = sec_of(orig, o[4]), sec_of(cand, c[4])
                if not so:
                    continue
                ln = None
                for j in range(k + 1, min(len(oi), k + 5)):
                    if oi[j][1] in (0xb7, 0x7a) and 0 < oi[j][4] < 4096 and oi[j][4] == ci[j][4]:
                        ln = oi[j][4]; break
                if so == '.rodata' and ln is None:
                    stats['rodata_unknown_len'] += 1; continue
                co, cc = content(orig, o[4], ln, so), content(cand, c[4], ln, sc)
                stats['lddw'] += 1; stats[f'sec:{so}'] += 1
                if so != sc or co != cc:
                    dd.append({'slot': o[0], 'sec': so, 'cand_sec': sc, 'orig_va': hex(o[4]), 'cand_va': hex(c[4]), 'len': ln,
                               'orig': repr(co)[:200], 'cand': repr(cc)[:200]})
            if best is None or len(dd) < len(best[1]):
                best = (nm, dd)
            if not dd:
                break
        nm, dd = best
        stats['windows'] += 1
        if dd:
            stats['windows_with_content_diff'] += 1; stats['content_diffs'] += len(dd)
            diffs.append({'start': hex(w['start']), 'symbol': nm, 'raw': r['raw'], 'diffs': dd})
    print(dict(stats))
    for d in diffs[:60]:
        print(d['start'], d['symbol'][:60], len(d['diffs']), [(x['sec'], x['orig'][:60], x['cand'][:60]) for x in d['diffs'][:2]])
    if a.json:
        Path(a.json).write_text(json.dumps({'stats': dict(stats), 'windows': diffs}, indent=1))


if __name__ == '__main__':
    main()
