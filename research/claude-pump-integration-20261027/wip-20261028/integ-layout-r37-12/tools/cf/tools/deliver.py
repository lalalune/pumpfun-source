#!/usr/bin/env python3
"""Write SC/deliveries/coordfiles-NN from a crate snapshot + its build dir (score.json must exist).
  deliver.py NN --src <crate dir> --build <build out dir> --readme README.md --summary "..." [--synthetic] [--synthetic-gains a,b]
"""
import argparse, hashlib, json, shutil, subprocess, sys
from pathlib import Path
SC = Path('/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work')
ap = argparse.ArgumentParser()
ap.add_argument('nn')
ap.add_argument('--src', type=Path, required=True)
ap.add_argument('--build', type=Path, required=True)
ap.add_argument('--readme', type=Path, required=True)
ap.add_argument('--summary', required=True)
ap.add_argument('--synthetic', action='store_true')
ap.add_argument('--synthetic-gains', default='')
ap.add_argument('--extra', nargs='*', default=[], help='extra files to copy into the delivery (tools, sitemap)')
a = ap.parse_args()
d = SC / 'deliveries' / f'coordfiles-{a.nn}'
assert not d.exists(), d
sc = json.loads((a.build / 'score.json').read_text())['summary']
assert not sc['losses'] and not sc['raw_losses'] and sc['gains'], sc
d.mkdir(parents=True)
shutil.copytree(a.src, d / 'src', ignore=shutil.ignore_patterns('target'))
base = SC / 'base' / 'current' / 'pump'
p = subprocess.run(['diff', '-ruN', str(base), str(a.src.resolve())], capture_output=True, text=True, cwd='/')
(d / 'patch.diff').write_text(p.stdout)
for f in ['unstripped.so', 'candidate.so', 'build.log', 'score.json']:
    shutil.copy2(a.build / f, d / f)
files = sorted(set(l[4:].split('\t')[0].replace(str(a.src.resolve()) + '/', '') for l in p.stdout.splitlines() if l.startswith('+++ ')))
round_ = (SC / 'base' / 'CURRENT_ROUND').read_text().strip()
dj = {'lane': 'coordfiles', 'base_round': round_,
      'base_unstripped_sha256': hashlib.sha256((SC / 'base/current/unstripped.so').read_bytes()).hexdigest(),
      'unstripped_sha256': hashlib.sha256((d / 'unstripped.so').read_bytes()).hexdigest(),
      'normalized': sc['normalized'], 'raw': sc['raw'], 'gains': sc['gains'], 'losses': sc['losses'],
      'raw_gains': sc['raw_gains'], 'raw_losses': sc['raw_losses'], 'synthetic_layout': a.synthetic,
      'synthetic_gains': [x for x in a.synthetic_gains.split(',') if x],
      'files_changed': files, 'summary': a.summary}
(d / 'delivery.json').write_text(json.dumps(dj, indent=1))
shutil.copy2(a.readme, d / 'README.md')
if a.extra:
    (d / 'tools').mkdir()
    for x in a.extra:
        shutil.copy2(x, d / 'tools' / Path(x).name)
print(json.dumps(dj, indent=1))
