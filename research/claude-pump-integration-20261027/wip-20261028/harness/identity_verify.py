#!/usr/bin/env python3
"""Verify the main-Pump toolchain-identity packet from repository files only (pure Python).

1. Manifest hashes.
2. For the original and every packaged ELF: extract the 128-bit constants returned by the five
   original TypeId thunk windows (0xce50, 0x188cc8, 0x19a1a0, 0x1a8e28 = alloc StringError's
   core::error::Error::type_id; 0x1ab9b8 = libcore NoPayload's Any::type_id) and every same-shape
   thunk in the candidates (lddw r2; stxdw [r1+8]; lddw r2; stxdw [r1+0]; exit).
3. Recompute the normalized/raw window counts of every packaged ELF (scripts/pump_compare_function_bytes.py
   rule) and compare with BUILDS.json; the identity-recipe builds contain thunks returning exactly the
   original constants and the mac-recipe build does not.
"""
from pathlib import Path
import csv, gzip, hashlib, json, struct, sys
sys.dont_write_bytecode = True
P = Path(__file__).resolve().parent
ROOT = next(p for p in P.parents if (p / 'evidence/original/pump/deployed.so').is_file())
sys.path.insert(0, str(ROOT / 'scripts'))
from pump_compare_function_bytes import normalize, body  # noqa
from pump_quote_control_function_match import sections  # noqa
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
THUNKS = [0xce50, 0x188cc8, 0x19a1a0, 0x1a8e28, 0x1ab9b8]


def elf_functions(blob):
    shoff, = struct.unpack_from('<Q', blob, 0x28); shentsize, shnum, shstrndx = struct.unpack_from('<HHH', blob, 0x3a)
    hdrs = [struct.unpack_from('<IIQQQQIIQQ', blob, shoff + i * shentsize) for i in range(shnum)]
    names = hdrs[shstrndx]
    secname = lambda off: blob[names[4] + off:blob.index(b'\0', names[4] + off)].decode()
    ti = next(i for i, h in enumerate(hdrs) if secname(h[0]) == '.text')
    out = []
    for h in hdrs:
        if h[1] != 2:
            continue
        st = hdrs[h[6]]
        for k in range(h[5] // 24):
            n, info, other, shndx, value, size = struct.unpack_from('<IBBHQQ', blob, h[4] + k * 24)
            if info & 0xf == 2 and shndx == ti and size:
                out.append((value, size, blob[st[4] + n:blob.index(b'\0', st[4] + n)].decode()))
    return out


def thunk_value(raw):
    """(hi, lo) if raw is `lddw r2,A; stxdw [r1+8],r2; lddw r2,B; stxdw [r1+0],r2; exit`."""
    if len(raw) != 56 or raw[0] != 0x18 or raw[24] != 0x18 or raw[48] != 0x95:
        return None
    if raw[16:20] != bytes([0x7b, 0x21, 0x08, 0x00]) or raw[40:44] != bytes([0x7b, 0x21, 0x00, 0x00]):
        return None
    q = lambda i: struct.unpack_from('<I', raw, i + 4)[0] | struct.unpack_from('<I', raw, i + 12)[0] << 32
    return (q(0), q(24))


def windows(orig, os_, elf):
    cs = sections(elf); by = {}
    for start, length, name in elf_functions(elf):
        raw = body(elf, cs, start, length); nrm, _ = normalize(raw, start, cs)
        by.setdefault((length, hashlib.sha256(nrm).hexdigest()), []).append(hashlib.sha256(raw).hexdigest())
    n = r = 0; matched = set()
    with (ROOT / 'repro/reconstruction-status-2026-10-26/functions.tsv').open() as fh:
        for row in csv.DictReader(fh, delimiter='\t'):
            if row['program'] != 'pump' or row['variant'] != 'selected':
                continue
            s, e = int(row['original_start']), int(row['original_end']); raw = body(orig, os_, s, e - s); nrm, _ = normalize(raw, s, os_)
            ms = by.get((e - s, hashlib.sha256(nrm).hexdigest()), [])
            if ms:
                n += 1; matched.add(s)
            r += hashlib.sha256(raw).hexdigest() in ms
    return n, r, matched


def main():
    manifest = json.loads((P / 'MANIFEST.json').read_text())
    actual = {str(f.relative_to(P)) for f in P.rglob('*') if f.is_file() and '__pycache__' not in f.parts}
    assert actual == set(manifest) | {'MANIFEST.json'}, sorted(actual ^ (set(manifest) | {'MANIFEST.json'}))
    for name, digest in manifest.items():
        assert sha(P / name) == digest, name
    orig = (ROOT / 'evidence/original/pump/deployed.so').read_bytes(); os_ = sections(orig)
    want = {}
    for s in THUNKS:
        v = thunk_value(body(orig, os_, s, 56)); assert v, hex(s); want[s] = v
    builds = json.loads((P / 'BUILDS.json').read_text())
    report = {'original_thunks': {hex(s): [f'{v[0]:016x}', f'{v[1]:016x}'] for s, v in want.items()}, 'builds': {}}
    for b in builds:
        elf = gzip.decompress((P / b['unstripped']).read_bytes()); assert hashlib.sha256(elf).hexdigest() == b['unstripped_sha256']
        cs = sections(elf)
        vals = {thunk_value(body(elf, cs, s, n)) for s, n, _ in elf_functions(elf) if n == 56} - {None}
        has_all = all(v in vals for v in want.values())
        n, r, matched = windows(orig, os_, elf)
        assert (n, r) == (b['normalized'], b['raw']), (b['name'], n, r)
        assert has_all == b['original_typeids_present'], b['name']
        assert all(s in matched for s in THUNKS) == has_all, b['name']
        report['builds'][b['name']] = {'recipe': b['recipe'], 'normalized': n, 'raw': r, 'original_typeids_present': has_all}
    print(json.dumps({'verified': True, **report}, indent=1))


if __name__ == '__main__':
    main()
