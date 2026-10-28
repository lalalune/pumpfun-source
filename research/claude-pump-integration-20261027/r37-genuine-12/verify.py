#!/usr/bin/env python3
"""Verify this main-Pump research package from repository files only.

Checks: manifest hashes; the build record binds both ELFs and the packaged source;
source.patch turns the base round's archived primary source into the packaged source;
the window inventory recomputed from unstripped.so equals inventory.json.gz and RESULT.json
(normalization = scripts/pump_compare_function_bytes.py); gains/losses vs the base round's
inventory; and, when present, the 44-suite regression report binds this candidate with no
mismatches.
"""
from pathlib import Path
import csv, gzip, hashlib, json, sys
sys.dont_write_bytecode = True
P = Path(__file__).resolve().parent
ROOT = next(p for p in P.parents if (p / 'evidence/original/pump/deployed.so').is_file())
sys.path.insert(0, str(ROOT / 'scripts'))
from pump_compare_function_bytes import normalize, body  # noqa
from pump_quote_control_function_match import sections  # noqa
import difflib


def tree_files(root):
    root = Path(root)
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob('*')) if p.is_file()}


def tree_diff(base, new, prefix='programs/pump'):
    """Deterministic unified diff of two crate trees (text files), pure Python."""
    a, b = tree_files(base), tree_files(new)
    out = []
    for rel in sorted(set(a) | set(b)):
        x, y = a.get(rel), b.get(rel)
        if x == y:
            continue
        xl = x.decode().splitlines(keepends=True) if x is not None else []
        yl = y.decode().splitlines(keepends=True) if y is not None else []
        fa = f'a/{prefix}/{rel}' if x is not None else '/dev/null'
        fb = f'b/{prefix}/{rel}' if y is not None else '/dev/null'
        for line in difflib.unified_diff(xl, yl, fa, fb, n=3):
            out.append(line if line.endswith('\n') else line + '\n\\ No newline at end of file\n')
    return ''.join(out)


sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(gzip.decompress(p.read_bytes()) if p.read_bytes()[:2] == b'\x1f\x8b' else p.read_bytes())


def elf_functions(blob):
    """FUNC symbols in .text from the ELF symbol table (no external tools)."""
    import struct
    shoff, = struct.unpack_from('<Q', blob, 0x28); shentsize, shnum, shstrndx = struct.unpack_from('<HHH', blob, 0x3a)
    hdrs = [struct.unpack_from('<IIQQQQIIQQ', blob, shoff + i * shentsize) for i in range(shnum)]
    names = hdrs[shstrndx]
    secname = lambda off: blob[names[4] + off:blob.index(b'\0', names[4] + off)].decode()
    text_index = next(i for i, h in enumerate(hdrs) if secname(h[0]) == '.text')
    out = []
    for h in hdrs:
        if h[1] != 2:  # SHT_SYMTAB
            continue
        strtab = hdrs[h[6]]
        for k in range(h[5] // 24):
            st_name, st_info, st_other, st_shndx, st_value, st_size = struct.unpack_from('<IBBHQQ', blob, h[4] + k * 24)
            if st_info & 0xf == 2 and st_shndx == text_index and st_size:
                nm = blob[strtab[4] + st_name:blob.index(b'\0', strtab[4] + st_name)].decode()
                out.append((st_value, st_size, nm))
    return out


def main():
    manifest = json.loads((P / 'MANIFEST.json').read_text())
    actual = {str(f.relative_to(P)) for f in P.rglob('*') if f.is_file() and '__pycache__' not in f.parts}
    assert actual == set(manifest) | {'MANIFEST.json'}, sorted(actual ^ (set(manifest) | {'MANIFEST.json'}))
    for name, digest in manifest.items():
        assert not (P / name).is_symlink() and sha(P / name) == digest, name
    res = json.loads((P / 'RESULT.json').read_text())
    base = ROOT / res['base_round_package']
    bcp = json.loads((base / 'CHECKPOINT.json').read_text())
    assert bcp['candidate_sha256'] == res['base_candidate_sha256'] and bcp['unstripped_sha256'] == res['base_unstripped_sha256']
    rec = json.loads((P / 'build-comparison.json').read_text())
    assert rec['returncode'] == 0 and rec['source_unchanged'] and rec['workspace_layout']
    assert rec['comparison']['candidate_sha256'] == sha(P / 'candidate.so') == res['candidate_sha256']
    assert rec['unstripped_sha256'] == sha(P / 'unstripped.so') == res['unstripped_sha256']
    assert rec['comparison']['full_byte_equality'] is False
    crate = P / 'source/programs/pump'
    for k, v in rec['primary_source_sha256'].items():
        assert sha(ROOT / k) == v, k
    packaged = {str(f.relative_to(crate)) for f in crate.rglob('*') if f.is_file()}
    assert {str(Path(k).relative_to(crate.relative_to(ROOT))) for k in rec['primary_source_sha256']} == packaged
    assert tree_diff(base / 'primary', crate) == (P / 'source.patch').read_text(), 'source.patch is not the exact difference from the base primary source'
    orig = (ROOT / 'evidence/original/pump/deployed.so').read_bytes(); os_ = sections(orig)

    def windows(elf_path):
        cand = elf_path.read_bytes(); cs = sections(cand)
        by = {}
        for start, length, name in elf_functions(cand):
            raw = body(cand, cs, start, length); nrm, _ = normalize(raw, start, cs)
            by.setdefault((length, hashlib.sha256(nrm).hexdigest()), []).append((start, name, hashlib.sha256(raw).hexdigest()))
        rows = {}
        with (ROOT / 'repro/reconstruction-status-2026-10-26/functions.tsv').open() as fh:
            for r in csv.DictReader(fh, delimiter='\t'):
                if r['program'] != 'pump' or r['variant'] != 'selected':
                    continue
                s, e = int(r['original_start']), int(r['original_end']); raw = body(orig, os_, s, e - s); nrm, _ = normalize(raw, s, os_)
                ms = by.get((e - s, hashlib.sha256(nrm).hexdigest()), [])
                rows[s] = (bool(ms), any(m[2] == hashlib.sha256(raw).hexdigest() for m in ms), e - s, {m[0] for m in ms})
        return rows

    def counts_of(rows):
        return {'total': len(rows), 'raw': sum(v[1] for v in rows.values()), 'normalized': sum(v[0] for v in rows.values()),
                'unmatched': sum(not v[0] for v in rows.values()), 'matched_text_bytes': sum(v[2] for v in rows.values() if v[0])}

    def check_inventory(rows, inv):
        for w in inv['windows']:
            n, rw, b, starts = rows[w['start']]
            assert n == bool(w['normalized_matches']) and rw == w['raw_match'] and b == w['bytes'], hex(w['start'])
            assert starts == {m['start'] for m in w['normalized_matches']}, hex(w['start'])
        assert counts_of(rows) == inv['counts'], (counts_of(rows), inv['counts'])

    rows = windows(P / 'unstripped.so')
    inv = read(P / 'inventory.json.gz'); assert inv['candidate_sha256'] == res['unstripped_sha256']
    check_inventory(rows, inv)
    counts = counts_of(rows)
    assert counts == res['counts'], (counts, res['counts'])
    if (P / 'control').is_dir():
        ccrate = P / 'control/source/programs/pump'
        assert tree_diff(base / 'primary', ccrate) == '', 'control source differs from the base primary source'
        crec = json.loads((P / 'control/build-comparison.json').read_text())
        assert crec['returncode'] == 0 and crec['source_unchanged'] and crec['workspace_layout']
        assert crec['comparison']['candidate_sha256'] == sha(P / 'control/candidate.so') and crec['unstripped_sha256'] == sha(P / 'control/unstripped.so')
        prof = lambda r: (r.get('target_library_profile') or {}).get('profile', (r.get('target_library_profile') or {}).get('name'))
        assert crec['selected_toolchain'] == rec['selected_toolchain'] and crec['workspace_layout'] == rec['workspace_layout'], 'control and candidate builds must use the same toolchain/layout'
        assert bool(crec.get('target_library_profile')) == bool(rec.get('target_library_profile')) and prof(crec) == prof(rec), 'control and candidate builds must use the same target-library profile'
        crows = windows(P / 'control/unstripped.so'); check_inventory(crows, read(P / 'control/inventory.json.gz'))
        assert counts_of(crows) == res['base_counts']
        bn = {s for s, v in crows.items() if v[0]}; br = {s for s, v in crows.items() if v[1]}
    else:
        binv = read(base / 'inventory.json.gz')
        bn = {w['start'] for w in binv['windows'] if w['normalized_matches']}; br = {w['start'] for w in binv['windows'] if w['raw_match']}
    cn = {s for s, v in rows.items() if v[0]}; cr = {s for s, v in rows.items() if v[1]}
    assert [hex(x) for x in sorted(cn - bn)] == res['normalized_gains'] and [hex(x) for x in sorted(bn - cn)] == res['normalized_losses']
    assert [hex(x) for x in sorted(cr - br)] == res['raw_gains'] and [hex(x) for x in sorted(br - cr)] == res['raw_losses']
    codex = read(base / 'inventory.json.gz'); kn = {w['start'] for w in codex['windows'] if w['normalized_matches']}
    assert [hex(x) for x in sorted(cn - kn)] == res['normalized_gains_vs_codex_round'] and [hex(x) for x in sorted(kn - cn)] == res['normalized_losses_vs_codex_round']
    reg = None
    if (P / 'regression-suites.json.gz').exists():
        rep = read(P / 'regression-suites.json.gz')
        assert rep['candidate_sha256'] == res['candidate_sha256']
        import pump_validate_all as base
        from pump_diagnostic_audit import audit
        assert set(rep['suites']) == {n for n, _ in base.SUITES}
        assert rep['case_count'] == sum(base.EXPECTED_CASES[n] for n in rep['suites']) == res['regression']['cases']
        a = audit(rep['suites']); assert not a['mismatches'] and a['log_bearing_cases'] == res['regression']['paired_log_cases']
        reg = {'suites': len(rep['suites']), 'cases': rep['case_count'], 'paired_log_cases': a['log_bearing_cases'], 'mismatches': 0}
    if (P / 'full.json.gz').exists():
        rep = read(P / 'full.json.gz')
        assert rep['candidate_sha256'] == res['candidate_sha256']
        assert len(rep['suites']) == 44 and rep['case_count'] == res['regression']['cases']
        from pump_diagnostic_audit import audit
        a = audit(rep['suites']); assert not a['mismatches']
        reg = {'suites': len(rep['suites']), 'cases': rep['case_count'], 'paired_log_cases': a['log_bearing_cases']}
    print(json.dumps({'verified': True, 'counts': counts, 'normalized_gains': res['normalized_gains'], 'raw_gains': res['raw_gains'],
                      'losses': res['normalized_losses'] + res['raw_losses'], 'regression': reg, 'whole_elf_equal': False}, indent=1))


if __name__ == '__main__':
    main()
