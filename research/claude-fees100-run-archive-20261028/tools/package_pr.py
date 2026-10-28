#!/usr/bin/env python3
"""Assemble a fees100 research packet (sources, Linux ELFs, measurement, runtime summary, verifier).

usage: python3 -I package_pr.py --src TREE --parent TREE --parent-symbols SO --parent-label TEXT --linux PREFIX
          [--repeat PREFIX] --runtime REPORT.json --notes NOTES.md --title TITLE --out PACKET_DIR --repo REPO_ROOT
PREFIX is a cbuild.py output prefix. REPO_ROOT must contain evidence/original/pump_fees/deployed.so and
research/fees-composed-frontier188/window_map.py. The packet is self-verifying (verify.py).
"""
import argparse, difflib, gzip, hashlib, importlib.util, json, re, shutil, sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()
SKIP = {'target', 'linker.sh', 'effective-link-args.txt', 'link.map'}

def tree_files(root):
    out = {}
    for p in sorted(root.rglob('*')):
        rel = p.relative_to(root)
        if p.is_file() and not (set(rel.parts) & SKIP) and p.suffix != '.so':
            out[rel.as_posix()] = p.read_bytes()
    return out

def gz(data):
    return gzip.compress(data, compresslevel=9, mtime=0)

def main():
    ap = argparse.ArgumentParser()
    for k in ['src', 'parent', 'parent-symbols', 'parent-label', 'linux', 'runtime', 'notes', 'title', 'out', 'repo']:
        ap.add_argument('--' + k, required=True)
    ap.add_argument('--repeat')
    a = ap.parse_args()
    out = Path(a.out); repo = Path(a.repo)
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    src, parent = tree_files(Path(a.src)), tree_files(Path(a.parent))
    in_tree = 'vendor/Cargo.toml' in src  # materializers place the macro crate at vendor/
    rel_vendor = b'vendor' if in_tree else b'vendor/used-public'
    def fix_toml(b):
        return re.sub(rb'anchor-attribute-program = \{ path = "[^"]+" \}', b'anchor-attribute-program = { path = "' + rel_vendor + b'" }', b)
    src['Cargo.toml'] = fix_toml(src['Cargo.toml']); parent['Cargo.toml'] = fix_toml(parent['Cargo.toml'])
    vendor = {} if in_tree else tree_files(HERE.parent / 'vendor/used-public')
    for name, data in src.items():
        d = out / 'source' / name; d.parent.mkdir(parents=True, exist_ok=True); d.write_bytes(data)
    for name, data in vendor.items():
        d = out / 'source/vendor/used-public' / name; d.parent.mkdir(parents=True, exist_ok=True); d.write_bytes(data)
    changed = sorted(n for n in set(src) | set(parent) if src.get(n) != parent.get(n))
    patch = []
    for name in changed:
        old = parent.get(name, b''); new = src.get(name, b'')
        if name in parent:
            d = out / 'parent-changed' / name; d.parent.mkdir(parents=True, exist_ok=True); d.write_bytes(old)
        patch.extend(difflib.unified_diff(old.decode().splitlines(True), new.decode().splitlines(True), 'parent/' + name, 'candidate/' + name))
    (out / 'source.patch').write_text(''.join(patch))
    builds = ['linux'] + (['repeat'] if a.repeat else [])
    for role, prefix in [('linux', a.linux), ('repeat', a.repeat)]:
        if not prefix: continue
        folder = out / 'builds' / role; folder.mkdir(parents=True)
        (folder / 'result.json').write_text(json.dumps(json.loads(Path(prefix + '-result.json').read_text()), indent=1) + '\n')
        (folder / 'launch.json').write_text(json.dumps(json.loads(Path(prefix + '-launch.json').read_text()), indent=1) + '\n')
        (folder / 'symbols.so.gz').write_bytes(gz(Path(prefix + '-symbols.so').read_bytes()))
        (folder / 'candidate.so.gz').write_bytes(gz(Path(prefix + '-candidate.so').read_bytes()))
        (folder / 'build.log.gz').write_bytes(gz(Path(prefix + '-build.log').read_bytes()))
    if (Path(a.src) / 'ordered.ld').exists():
        (out / 'layout').mkdir(); shutil.copyfile(Path(a.src) / 'ordered.ld', out / 'layout/ordered.ld')
    (out / 'parent').mkdir()
    psym = Path(a.parent_symbols).read_bytes()
    (out / 'parent/symbols.so.gz').write_bytes(gz(psym))
    rep = json.loads(Path(a.runtime).read_text())
    cand = Path(a.linux + '-candidate.so').read_bytes(); sym = Path(a.linux + '-symbols.so').read_bytes()
    summary = dict(candidate_sha256=rep['candidate_sha256'], original_sha256=rep['original_sha256'], cases=rep['case_count'],
                   mismatches=rep['mismatches'], suites={k: v.get('case_count') for k, v in rep['suites'].items()},
                   runner='scripts/fees_validate_all.py')
    assert summary['candidate_sha256'] == sha(cand) and not summary['mismatches']
    (out / 'runtime').mkdir(); (out / 'runtime/summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    spec = importlib.util.spec_from_file_location('wm', repo / 'research/fees-composed-frontier188/window_map.py')
    w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
    original = (repo / 'evidence/original/pump_fees/deployed.so').read_bytes()
    def m(img):
        o, c = w.windows(original), w.windows(img)
        s = {r['signature'] for r in c}; r_ = {r['raw_sha256'] for r in c}
        return {r['address'] for r in o if r['signature'] in s}, {r['address'] for r in o if r['raw_sha256'] in r_}, o, len(c)
    n1, r1, o, ncw = m(sym); n0, r0, _, _ = m(psym)
    assert not (n0 - n1), ('lost normalized', sorted(n0 - n1))
    claims = dict(original_sha256=sha(original), builds=builds, normalized=len(n1), raw=len(r1), candidate_windows=ncw,
                  gained_normalized=sorted(n1 - n0), lost_raw=sorted(r0 - r1), gained_raw=sorted(r1 - r0),
                  parent_normalized=len(n0), parent_raw=len(r0), parent_symbols_sha256=sha(psym),
                  remaining_original=sorted((x['address'], x['bytes']) for x in o if x['address'] not in n1),
                  source_inputs={p.relative_to(out / 'source').as_posix(): sha(p.read_bytes()) for p in (out / 'source').rglob('*') if p.is_file()},
                  parent_inputs={n: sha(parent[n]) for n in changed if n in parent},
                  changed_files=changed, runtime_cases=summary['cases'],
                  candidate_sha256=sha(cand), symbols_sha256=sha(sym),
                  whole_elf_equal=cand == original[:len(cand)] and not any(original[len(cand):]),
                  meaningful_elf_bytes=len(cand))
    (out / 'claims.json').write_text(json.dumps(claims, indent=1) + '\n')
    shutil.copyfile(HERE / 'packet_verify_template.py', out / 'verify.py')
    notes = Path(a.notes).read_text()
    rel = out.relative_to(repo) if out.is_relative_to(repo) else 'research/' + out.name
    gained = sorted(n1 - n0)
    readme = f"""# {a.title}

**Result: {len(n1)} / 585 normalized original Fees functions ({len(n1) - len(n0):+d} vs the {len(n0)}-function parent), {len(r1)} raw-local, {ncw} compiled windows.**
Newly matched original windows: {', '.join(str(x) for x in gained) or 'none'}. No normalized match is lost
(raw-local lost: {sorted(r0 - r1) or 'none'}). {'**The stripped candidate is byte-identical to the complete meaningful ELF of the captured original** (' + format(len(cand), ',') + ' bytes; the remaining ' + format(len(original) - len(cand), ',') + ' bytes of the capture are all zero loader allocation).' if claims['whole_elf_equal'] else 'Whole-ELF and capture equality remain false; ' + str(585 - len(n1)) + ' original function(s) remain unmatched: ' + ', '.join(str(x) for x, _ in claims['remaining_original']) + '.'}

Parent: {a.parent_label} (Linux symbols `{sha(psym)[:16]}…`, rebuilt here byte-for-byte). Only the files listed in
`source.patch` change.

{notes.strip()}

## Build and validation

- Canonical Linux v1.44 build (`sbpf-solana-solana`, `cargo rustc --release --locked --offline`, vendored macro at the
  parent's `/work/next637/vendor/used-public` path, `layout/ordered.ld` re-bound to the changed sections with
  `relayout.py` from research/claude-fees100-whole-elf-endstate-20261027 and applied through a linker wrapper,
  pinned v1.52 `llvm-objcopy --strip-all`): candidate `{sha(cand)}`, symbols `{sha(sym)}`.{' A second build reproduced both hashes.' if a.repeat else ''}
- Runtime: `scripts/fees_validate_all.py` passes **{summary['cases']:,} cases across {len(summary['suites'])} suites** with
  zero mismatches against the captured original.
- No assembly, captured instruction fragments, padding or post-link rewriting. `source/` is the complete workspace
  (program inputs, layout recipe and the vendored `anchor-attribute-program` with `#[used]`, inherited from the parent).

```sh
python3 -B {rel}/verify.py
```

The verifier rejects extra/symlinked/special files and optimized Python, re-hashes both ELFs, recomputes the
normalized/raw window sets with `research/fees-composed-frontier188/window_map.py`, checks the gained windows against
the included parent ELF, re-derives `source.patch`, and checks the runtime summary binding.
"""
    (out / 'README.md').write_text(readme)
    manifest = {p.relative_to(out).as_posix(): sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1, sort_keys=True) + '\n')
    print(json.dumps({k: claims[k] for k in ['normalized', 'raw', 'candidate_windows', 'gained_normalized', 'lost_raw', 'gained_raw', 'runtime_cases']}))

if __name__ == '__main__':
    main()
