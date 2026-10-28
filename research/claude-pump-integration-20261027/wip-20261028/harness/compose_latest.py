#!/usr/bin/env python3
"""Compose the newest cumulative delivery of every lane onto a base and build/score it.

  compose_latest.py --name NAME [--base r37g4] [--pre PATCH ...] [--lanes bodyloA,bodyloB,libnear3]

Starts from W/base/<base>/pump, applies each --pre git patch (e.g. a peer's source-on-r37g4.patch,
`git apply -p1` in the crate), then the latest W/deliveries/<lane>-NN/src of each lane (diffed
against the base it was derived from) via integrate.py, builds with the identity recipe and scores.
"""
import argparse, json, re, shutil, subprocess, sys
from pathlib import Path

H = Path(__file__).resolve().parent
W = H.parent


def latest(lane):
    ds = [d for d in (W / 'deliveries').glob(f'{lane}-*') if re.fullmatch(rf'{re.escape(lane)}-\d+', d.name) and (d / 'delivery.json').exists()]
    ds = [d for d in ds if json.loads((d / 'delivery.json').read_text()).get('runtime_valid', True)]
    return max(ds, key=lambda d: int(d.name.rsplit('-', 1)[1])) if ds else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--name', required=True)
    ap.add_argument('--base', default='r37g4')
    ap.add_argument('--pre', action='append', default=[])
    ap.add_argument('--lanes', default='bodyloA,bodyloB,libnear3')
    a = ap.parse_args()
    base = W / 'base' / a.base / 'pump'
    pre = W / 'integ' / (a.name + '-pre')
    if pre.exists():
        shutil.rmtree(pre)
    shutil.copytree(base, pre / 'src')
    for p in a.pre:
        subprocess.run(['git', 'apply', '-p1', str(Path(p).resolve())], cwd=pre / 'src', check=True)
    parts = []
    for lane in a.lanes.split(','):
        d = latest(lane)
        if d:
            parts += ['--part', f'{lane}={d}/src', '--base-of', f'{lane}={base}']
            print('using', d.name, file=sys.stderr)
    r = subprocess.run([sys.executable, str(H / 'integrate.py'), '--name', a.name, '--base-src', str(pre / 'src'), *parts], capture_output=True, text=True)
    rep = json.loads((W / 'integ' / a.name / 'report.json').read_text())
    b = rep.get('build') or {}; s = rep.get('score') or {}
    print(json.dumps({'build': {k: b.get(k) for k in ['ok', 'runtime_valid', 'stack_warnings', 'unstripped_sha256']},
                      'score': {k: s.get(k) for k in ['normalized', 'raw', 'gains', 'losses', 'raw_losses']},
                      'parts': [(p['label'], p['status']) for p in rep['parts']]}, indent=1))


if __name__ == '__main__':
    main()
