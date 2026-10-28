#!/usr/bin/env python3
"""deliver_r37.py <name> --build <builds/bNN> --readme <md> --summary ".." [--genuine-gains 0x..,..] [--genuine-only]
Writes W/deliveries/<name> from a bld.sh build dir (src snapshot, unstripped/candidate/build.log, score.json vs round37,
score_vs_base.json vs the r37g5 base). Refuses losses / raw losses vs the base, stack warnings, or a padded tree for a
genuine-only delivery."""
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path
W = Path('/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work')
L = W / 'lanes/integ-layout'
BASE_SRC = W / 'integ/r37g5/src'
BASE_SO = W / 'integ/r37g5/build/unstripped.so'
ap = argparse.ArgumentParser()
ap.add_argument('name'); ap.add_argument('--build', type=Path, required=True); ap.add_argument('--readme', type=Path, required=True)
ap.add_argument('--summary', required=True); ap.add_argument('--genuine-gains', default=''); ap.add_argument('--genuine-only', action='store_true'); ap.add_argument('--prev', default='', help='previous delivery of the same kind: refuse any window it matched that this build does not')
a = ap.parse_args()
b = a.build.resolve(); d = W / 'deliveries' / a.name
assert not d.exists(), d
fb = json.loads((b / 'fastbuild.json').read_text())
assert fb.get('ok') and fb.get('runtime_valid') is True and not fb.get('stack_warnings'), fb
s37 = json.loads((b / 'score.json').read_text())['summary']
sb = json.loads((b / 'score_vs_base.json').read_text())['summary']
assert sb['gains'] and not sb['losses'] and not sb['raw_losses'], sb
if a.prev:
    pw = json.loads((W / 'deliveries' / a.prev / 'score.json').read_text())['windows']
    cw = json.loads((b / 'score.json').read_text())['windows']
    lost = [hex(int(k)) for k, v in pw.items() if v['normalized'] and not cw[k]['normalized']]
    rlost = [hex(int(k)) for k, v in pw.items() if v['raw'] and not cw[k]['raw']]
    assert not lost and not rlost, ('losses vs', a.prev, lost, rlost)
pads = subprocess.run(['grep', '-rl', 'layout-pad', str(b / 'src')], capture_output=True, text=True).stdout.split()
if a.genuine_only:
    assert not pads, pads
d.mkdir(parents=True)
shutil.copytree(b / 'src', d / 'src', ignore=shutil.ignore_patterns('target'))
p = subprocess.run(['diff', '-ruN', str(BASE_SRC), str((d / 'src').resolve())], capture_output=True, text=True, cwd='/')
(d / 'patch.diff').write_text(p.stdout)
for f in ['unstripped.so', 'candidate.so', 'build.log', 'score.json', 'score_vs_base.json']:
    shutil.copy2(b / f, d / f)
files = sorted(set(l[4:].split('\t')[0].replace(str((d / 'src').resolve()) + '/', '') for l in p.stdout.splitlines() if l.startswith('+++ ')))
gen = [x for x in a.genuine_gains.split(',') if x]
dj = {'lane': 'integ-layout', 'base_round': 'r37g5',
      'base_unstripped_sha256': hashlib.sha256(BASE_SO.read_bytes()).hexdigest(),
      'unstripped_sha256': hashlib.sha256((d / 'unstripped.so').read_bytes()).hexdigest(),
      'candidate_sha256': hashlib.sha256((d / 'candidate.so').read_bytes()).hexdigest(),
      'scored_against': str(W / 'base/round37/inventory.json'),
      'normalized': s37['normalized'], 'raw': s37['raw'],
      'gains': s37['gains'], 'losses': s37['losses'], 'raw_gains': s37['raw_gains'], 'raw_losses': s37['raw_losses'],
      'base_normalized': 788, 'base_raw': 165,
      'gains_vs_base': sb['gains'], 'losses_vs_base': sb['losses'], 'raw_gains_vs_base': sb['raw_gains'], 'raw_losses_vs_base': sb['raw_losses'],
      'synthetic_layout': not a.genuine_only,
      'genuine_gains_vs_base': [g for g in sb['gains'] if a.genuine_only or g in gen],
      'synthetic_gains_vs_base': [] if a.genuine_only else [g for g in sb['gains'] if g not in gen],
      'files_changed': files, 'summary': a.summary, 'previous_delivery': a.prev or None,
      'runtime_valid': fb.get('runtime_valid'), 'stack_warnings': fb.get('stack_warnings')}
(d / 'delivery.json').write_text(json.dumps(dj, indent=1))
shutil.copy2(a.readme, d / 'README.md')
shutil.copytree(L / 'tools', d / 'tools', ignore=shutil.ignore_patterns('__pycache__', '*.pkl'))
for f in sorted(p.name for p in (L / 'work').glob('sitemap_r37_*.json'))[-2:]:
    if (L / 'work' / f).exists():
        shutil.copy2(L / 'work' / f, d / 'tools' / f)
print(json.dumps({k: v for k, v in dj.items() if k not in ('gains', 'raw_gains', 'files_changed', 'synthetic_gains_vs_base', 'gains_vs_base')}, indent=1))
print('gains_vs_base', len(sb['gains']))
