#!/usr/bin/env python3
"""One-shot: correctly laid-out Linux container build of a CHANGED Fees source tree.

usage: python3 -I relayout_build.py SRC_DIR OUT_PREFIX [--ref NAME] [--ref-ld LD --ref-map MAP --ref-symbols SYM]
                                     [--stale LBUILD_PREFIX   (reuse an lbuild.py output of SRC_DIR; no compile)]

  1. lbuild.py  SRC_DIR with the reference ordered.ld (stale for the new source)   [one full container build]
  2. relayout.py reference (ld + map + symbols) -> stale build (map + symbols)    -> OUT_PREFIX.ld
  3. relink.py  the saved link inputs with OUT_PREFIX.ld (container rust-lld, ~3 s) -> OUT_PREFIX-{symbols,candidate}.so
  4. relayout.py --check (every selector matched once, nothing fell through, order kept)
  5. measure.py vs the reference symbols + elfinv.py summary            -> OUT_PREFIX-summary.json
The relinked output is byte-identical to a fresh cbuild.py of SRC_DIR with OUT_PREFIX.ld as its ordered.ld
(the compiler's objects do not depend on the linker script). To harvest, put OUT_PREFIX.ld into the tree as
ordered.ld. Reference default: the frontier named by R/shared/frontier/CURRENT (frontier/<n>/ordered.ld,
frontier/container/<n>.map, frontier/<n>-container-symbols.so).
"""
from pathlib import Path
import json, subprocess, sys
HERE = Path(__file__).resolve().parent
R = Path('/Users/shawwalters/fees100-run')
T = R / 'shared/tools'
def tool(name):
    return str(HERE / name) if (HERE / name).exists() else str(T / name)
def run(cmd, **kw):
    print('+', ' '.join(str(c) for c in cmd), flush=True)
    return subprocess.run([str(c) for c in cmd], **kw)

def main():
    argv = sys.argv[1:]
    opt = {}
    for k in ('--ref', '--ref-ld', '--ref-map', '--ref-symbols', '--stale'):
        if k in argv:
            i = argv.index(k); opt[k] = argv[i + 1]; del argv[i:i + 2]
    src, out = Path(argv[0]).resolve(), Path(argv[1]).resolve()
    name = opt.get('--ref') or (R / 'shared/frontier/CURRENT').read_text().strip()
    F = R / 'shared/frontier'
    ref_ld = Path(opt.get('--ref-ld') or F / name / 'ordered.ld')
    ref_map = Path(opt.get('--ref-map') or F / 'container' / f'{name}.map')
    ref_sym = Path(opt.get('--ref-symbols') or F / f'{name}-container-symbols.so')
    out.parent.mkdir(parents=True, exist_ok=True)
    if opt.get('--stale'):  # reuse an existing lbuild.py output prefix of SRC_DIR (skips the compile)
        stale = Path(opt['--stale']).resolve()
    else:
        stale = Path(str(out) + '-stale')
        r = run([sys.executable, '-I', tool('lbuild.py'), src, stale, '--ld', ref_ld])
        if r.returncode: sys.exit('lbuild failed: see ' + str(stale) + '-build.log')
    ld = Path(str(out) + '.ld')
    r = run([sys.executable, '-I', tool('relayout.py'), '--old-ld', ref_ld, '--old-map', ref_map, '--old-symbols', ref_sym,
             '--new-map', str(stale) + '.map', '--new-symbols', str(stale) + '-symbols.so', '--out', ld,
             '--report', str(out) + '-relayout.json'], stdout=subprocess.DEVNULL)
    if r.returncode: sys.exit('relayout failed')
    r = run([sys.executable, '-I', tool('relink.py'), stale, out, '--ld', ld])
    if r.returncode: sys.exit('relink failed: see ' + str(out) + '-link.log')
    chk = run([sys.executable, '-I', tool('relayout.py'), '--check', '--old-ld', ld, '--new-map', str(out) + '.map'],
              capture_output=True, text=True)
    meas = run([sys.executable, '-I', str(T / 'measure.py'), str(out) + '-symbols.so', '--baseline', ref_sym,
                '--json', str(out) + '-measure.json'], capture_output=True, text=True)
    inv = run([sys.executable, '-I', tool('elfinv.py'), str(out) + '-candidate.so', '--symbols', str(out) + '-symbols.so',
               '--json', str(out) + '-elfinv.json', '--quiet'], capture_output=True, text=True)
    m = json.loads(Path(str(out) + '-measure.json').read_text())
    rep = json.loads(Path(str(out) + '-relayout.json').read_text())
    e = json.loads(Path(str(out) + '-elfinv.json').read_text())
    s = dict(src=str(src), reference=dict(ld=str(ref_ld), map=str(ref_map), symbols=str(ref_sym)), ordered_ld=str(ld),
             relayout_counts=rep['counts'], window_moves=rep.get('window_moves'), text=rep.get('text'), data=rep.get('data'),
             dropped_old=rep['dropped_old'], unplaced_new=rep['unplaced_new'], check_ok=chk.returncode == 0,
             normalized=m['normalized'], raw_local=m['raw_local'], gained_normalized=m.get('gained_normalized'),
             lost_normalized=m.get('lost_normalized'), gained_raw=m.get('gained_raw'), lost_raw=m.get('lost_raw'),
             symbols_sha256=m['sha256'], whole_elf_equal=e['candidate']['equal_to_original_extent'],
             elf_independent_residuals=e['B_independent'], unmatched_bodies=e['unmatched_bodies'])
    Path(str(out) + '-summary.json').write_text(json.dumps(s, indent=1) + '\n')
    print(json.dumps({k: s[k] for k in ('relayout_counts', 'check_ok', 'normalized', 'raw_local', 'lost_normalized', 'lost_raw',
                                         'gained_normalized', 'whole_elf_equal')}, indent=1))
    print('ordered.ld ->', ld)
    return 0 if chk.returncode == 0 and not m.get('lost_normalized') else 1

if __name__ == '__main__':
    sys.exit(main())
