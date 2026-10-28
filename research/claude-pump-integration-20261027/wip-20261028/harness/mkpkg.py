#!/usr/bin/env python3
"""Build a promotion-ready main-Pump research package inside a repository worktree.

  mkpkg.py --name <pkg> --src <crate dir> --base roundNN [--title ...] [--lanes lanes.json] [--readme-extra md]
           [--control] [--builder-arg ARG ...] [--pkg-builder-arg ARG ...] [--expect-unstripped SHA]

Creates <PKG_WORKTREE>/research/claude-pump-integration-20261027/<pkg>/ with:
  source/programs/pump/...   composed crate (every top-level item except target/ and dotfiles)
  source.patch               exact pure-Python diff vs the base round's archived primary source
  candidate.so unstripped.so build-comparison.json build-attempt.json build.log.gz  (scripts/pump_build_verified.py)
  control/                   (--control) the same builder on the unchanged base primary source
  inventory.json.gz          Codex-format window inventory of unstripped.so
  RESULT.json verify.py README.md MANIFEST.json
"""
import argparse, gzip, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

H = Path(__file__).resolve().parent
SC = H.parent
FULL = Path(os.environ.get('PKG_WORKTREE', str(SC / 'int')))
PKGROOT = 'research/claude-pump-integration-20261027'
sys.path.insert(0, str(H))
from score import sections, normalize, body, candidate_functions, original_windows  # noqa
from treediff import tree_diff  # noqa
import fastbuild  # noqa


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def inventory(unstripped: Path):
    cand = unstripped.read_bytes(); cs = sections(cand)
    orig = (FULL / 'evidence/original/pump/deployed.so').read_bytes()
    by = {}
    for start, length, name in candidate_functions(unstripped):
        raw = body(cand, cs, start, length); nrm = normalize(raw, start, cs)
        by.setdefault((length, hashlib.sha256(nrm).hexdigest()), []).append(
            {'start': start, 'symbol': name, 'raw_sha256': hashlib.sha256(raw).hexdigest()})
    rows = []
    for w in original_windows():
        s, n = w['start'], w['bytes']
        ms = by.get((n, hashlib.sha256(w['norm']).hexdigest()), [])
        rh = hashlib.sha256(w['raw']).hexdigest()
        rows.append({'start': s, 'end': s + n, 'bytes': n, 'raw_sha256': rh,
                     'raw_match': any(m['raw_sha256'] == rh for m in ms), 'normalized_matches': ms})
    counts = {'total': len(rows), 'raw': sum(r['raw_match'] for r in rows),
              'normalized': sum(bool(r['normalized_matches']) for r in rows),
              'unmatched': sum(not r['normalized_matches'] for r in rows),
              'matched_text_bytes': sum(r['bytes'] for r in rows if r['normalized_matches'])}
    return {'original_sha256': hashlib.sha256(orig).hexdigest(), 'candidate_sha256': hashlib.sha256(cand).hexdigest(),
            'scope': 'Complete function windows; only internal direct-call operands and pointers into known ELF sections are masked (same rule as the Codex round inventories).',
            'windows': rows, 'counts': counts}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--name', required=True)
    ap.add_argument('--src', type=Path, required=True)
    ap.add_argument('--base', required=True)
    ap.add_argument('--title', default='')
    ap.add_argument('--lanes', type=Path)
    ap.add_argument('--readme-extra', type=Path)
    ap.add_argument('--expect-unstripped')
    ap.add_argument('--builder-arg', action='append', default=[])
    ap.add_argument('--pkg-builder-arg', action='append', default=[])
    ap.add_argument('--control', action='store_true')
    ap.add_argument('--extra-dir', action='append', default=[], help='name=path: copy a directory into the package (e.g. tools)')
    a = ap.parse_args()
    base_pkg = FULL / f'repro/pump/main-contract-{a.base}-20261027'
    assert base_pkg.is_dir(), base_pkg
    pkg = FULL / PKGROOT / a.name
    if pkg.exists():
        shutil.rmtree(pkg)
    crate = pkg / 'source/programs/pump'
    crate.mkdir(parents=True)
    for s in sorted(a.src.iterdir()):
        if s.name == 'target' or s.name.startswith('.'):
            continue
        if s.is_dir():
            shutil.copytree(s, crate / s.name, ignore=shutil.ignore_patterns('target', '.DS_Store'))
        else:
            shutil.copy2(s, crate / s.name)
    (pkg / 'source.patch').write_text(tree_diff(base_pkg / 'primary', crate))

    def verified_build(src_crate, outdir, extra=()):
        if outdir.exists():
            shutil.rmtree(outdir)
        outdir.parent.mkdir(parents=True, exist_ok=True)
        slot = fastbuild.acquire_slot(); t0 = time.time()
        try:
            r = subprocess.run([sys.executable, '-B', str(FULL / 'scripts/pump_build_verified.py'), '--source-directory', str(src_crate),
                                '--workspace-layout', '--registry-home', str(Path.home() / '.cargo'), '--output', str(outdir), *a.builder_arg, *extra],
                               cwd=FULL, capture_output=True, text=True)
        finally:
            slot.close()
        if r.returncode:
            sys.stdout.write(r.stdout[-3000:] + r.stderr[-3000:]); sys.exit('build failed: ' + str(src_crate))
        return round(time.time() - t0)

    out = FULL / 'work/claude-pkgbuild' / a.name  # the builder requires staging inside the repo (work/ is ignored)
    build_seconds = verified_build(crate, out, a.pkg_builder_arg)
    for f in ['candidate.so', 'unstripped.so', 'build-comparison.json', 'build-attempt.json']:
        shutil.copy2(out / f, pkg / f)
    (pkg / 'build.log.gz').write_bytes(gzip.compress((out / 'build.log').read_bytes(), mtime=0))
    stack = [l for l in (out / 'build.log').read_text().splitlines() if 'exceeded max offset' in l]
    assert not stack, 'runtime-invalid build (stack offset warning): ' + stack[0]
    us = sha(pkg / 'unstripped.so')
    if a.expect_unstripped:
        assert us == a.expect_unstripped, f'verified builder produced {us}, expected {a.expect_unstripped}'
    control = None
    if a.control:
        ccrate = pkg / 'control/source/programs/pump'
        shutil.copytree(base_pkg / 'primary', ccrate)
        cout = FULL / 'work/claude-pkgbuild' / ('control-' + a.base + '-' + hashlib.sha256(' '.join(a.builder_arg).encode()).hexdigest()[:12])
        cached = (cout / 'build-comparison.json').exists() and json.loads((cout / 'build-comparison.json').read_text()).get('returncode') == 0
        if cached:
            prev = json.loads((cout / 'build-comparison.json').read_text())
            rel = lambda k: k.split('/source/programs/pump/', 1)[-1]
            assert {rel(k): v for k, v in prev['primary_source_sha256'].items()} == {str(f.relative_to(ccrate)): sha(f) for f in ccrate.rglob('*') if f.is_file()}, 'cached control source mismatch'
            prev['primary_source_sha256'] = {str((ccrate / rel(k)).relative_to(FULL)): v for k, v in prev['primary_source_sha256'].items()}
            (cout / 'build-comparison.rebound.json').write_text(json.dumps(prev, indent=2) + '\n')
        else:
            verified_build(ccrate, cout)
        for f in ['candidate.so', 'unstripped.so']:
            shutil.copy2(cout / f, pkg / 'control' / f)
        shutil.copy2(cout / ('build-comparison.rebound.json' if cached else 'build-comparison.json'), pkg / 'control/build-comparison.json')
        control = inventory(pkg / 'control/unstripped.so')
        (pkg / 'control/inventory.json.gz').write_bytes(gzip.compress(json.dumps(control, indent=1).encode(), mtime=0))
    inv = inventory(pkg / 'unstripped.so')
    (pkg / 'inventory.json.gz').write_bytes(gzip.compress(json.dumps(inv, indent=1).encode(), mtime=0))
    codex_inv = json.loads(gzip.decompress((base_pkg / 'inventory.json.gz').read_bytes()))
    base_inv = control or codex_inv
    sel = lambda iv, k: {w['start'] for w in iv['windows'] if (w['normalized_matches'] if k == 'n' else w['raw_match'])}
    bn, br, cn, cr, kn = sel(base_inv, 'n'), sel(base_inv, 'r'), sel(inv, 'n'), sel(inv, 'r'), sel(codex_inv, 'n')
    cp = json.loads((base_pkg / 'CHECKPOINT.json').read_text())
    result = {'scope': 'Research package: composed main-Pump source on top of the maintained base round. Not a maintained checkpoint; whole-ELF identity remains false.',
              'base_round_package': f'repro/pump/main-contract-{a.base}-20261027',
              'base_candidate_sha256': cp['candidate_sha256'], 'base_unstripped_sha256': cp['unstripped_sha256'],
              'base_counts': base_inv['counts'], 'comparison_base': 'control build of the base primary source with the same builder' if control else 'base round inventory',
              'codex_round_counts': codex_inv['counts'],
              'normalized_gains_vs_codex_round': [hex(x) for x in sorted(cn - kn)], 'normalized_losses_vs_codex_round': [hex(x) for x in sorted(kn - cn)],
              'candidate_sha256': sha(pkg / 'candidate.so'), 'unstripped_sha256': us, 'counts': inv['counts'],
              'normalized_gains': [hex(x) for x in sorted(cn - bn)], 'normalized_losses': [hex(x) for x in sorted(bn - cn)],
              'raw_gains': [hex(x) for x in sorted(cr - br)], 'raw_losses': [hex(x) for x in sorted(br - cr)],
              'build': {'builder': 'scripts/pump_build_verified.py --workspace-layout ' + ' '.join(a.builder_arg), 'builder_args': a.builder_arg,
                        'builder_sha256': sha(FULL / 'scripts/pump_build_verified.py'), 'seconds': build_seconds, 'stack_offset_warnings': 0},
              'contributions': json.loads(a.lanes.read_text()) if a.lanes else [],
              'regression': None, 'whole_elf_equal': False, 'goal_complete': False}
    (pkg / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
    shutil.copy2(H / 'pkg_verify.py', pkg / 'verify.py')
    extra = a.readme_extra.read_text() if a.readme_extra else ''
    c, b0, k0 = inv['counts'], base_inv['counts'], codex_inv['counts']
    rows_md = f"| {a.base.capitalize()} as published (Codex pipeline, `{cp['candidate_sha256'][:8]}…`) | {k0['normalized']} | {k0['raw']} | {k0['unmatched']} | {k0.get('matched_text_bytes', cp.get('matched_text_bytes'))} |\n"
    if control:
        rows_md += f"| {a.base.capitalize()} primary, control build with this package's builder | {b0['normalized']} | {b0['raw']} | {b0['unmatched']} | {b0['matched_text_bytes']} |\n"
    rows_md += f"| This package (`{result['candidate_sha256'][:8]}…` / `{us[:8]}…`) | **{c['normalized']}** | **{c['raw']}** | {c['unmatched']} | **{c['matched_text_bytes']}** |"
    vs = 'the control build' if control else a.base.capitalize()
    readme = f"""# {a.title or a.name}

Research package composed on the maintained [{a.base.capitalize()}](../../../repro/pump/main-contract-{a.base}-20261027/README.md) main-Pump source. It is not a maintained checkpoint and does not edit `programs/pump`. **Whole-ELF identity remains false.**

| | normalized | raw | unmatched | matched text bytes |
|---|---:|---:|---:|---:|
{rows_md}

Normalized gains vs {vs}: {', '.join('`'+x+'`' for x in result['normalized_gains']) or 'none'}. Raw gains: {', '.join('`'+x+'`' for x in result['raw_gains']) or 'none'}. Losses: {', '.join(result['normalized_losses'] + result['raw_losses']) or '**none**'}. Against the published {a.base.capitalize()} inventory the package gains {len(result['normalized_gains_vs_codex_round'])} normalized windows and loses {len(result['normalized_losses_vs_codex_round'])}. Raw counts depend on link order: the published round applies derived text/data-order linker scripts, while both builds here use the plain link.

The candidate ELFs are included. `source/programs/pump` is the complete compiled crate and `source.patch` is its exact diff against the base round's archived `primary` source. Both ELFs come from the repository builder (`scripts/pump_build_verified.py --workspace-layout {' '.join(a.builder_arg)}`, v1.44 SDK, fresh target){', and `control/` holds the same builder applied to the unchanged base primary source' if control else ''}. The build log has no stack-offset warnings. `inventory.json.gz` uses the same window rule as the round inventories. The captured-loader regression corpus has not been run for this exact package yet.

```sh
python research/claude-pump-integration-20261027/{a.name}/verify.py
```

{extra}
"""
    (pkg / 'README.md').write_text(readme)
    for spec in a.extra_dir:
        nm, src = spec.split('=', 1)
        shutil.copytree(src, pkg / nm, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'target'))
    files = sorted(str(p.relative_to(pkg)) for p in pkg.rglob('*') if p.is_file() and p.name != 'MANIFEST.json')
    (pkg / 'MANIFEST.json').write_text(json.dumps({f: sha(pkg / f) for f in files}, indent=1) + '\n')
    print(json.dumps({k: result[k] for k in ['counts', 'base_counts', 'normalized_gains', 'normalized_losses', 'raw_losses', 'unstripped_sha256']}, indent=1))


if __name__ == '__main__':
    main()
