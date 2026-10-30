#!/usr/bin/env python3
"""capm.py --src CRATE --work WORK --out OUT : identity build with extra --emit=llvm-ir,mir (scratch only),
then score + target_metric like measure.sh. Keeps only swap_hop's IR/MIR. Prints one JSON line."""
import argparse, json, sys, shutil, subprocess, re
from pathlib import Path
H = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness')
sys.path.insert(0, str(H))
import fastbuild
ap = argparse.ArgumentParser()
ap.add_argument('--src', type=Path, required=True); ap.add_argument('--work', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True); ap.add_argument('--extra', default='')
ap.add_argument('--base', default=str(Path.home() / '.cache/pumpfun-reconstruction/w11/current-baseline/score.json'))
a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
extra = ['--emit=link,llvm-ir,mir'] + a.extra.split()
real = fastbuild.run_compiler
def run(cmd, *ra, **kw):
    if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[0]).endswith('/cargo') and cmd[1] == 'build':
        cmd = cmd[:]; cmd[1] = 'rustc'; cmd += ['--lib', '--'] + extra
    return real(cmd, *ra, **kw)
fastbuild.run_compiler = run
res = fastbuild.build(a.src, a.work, a.out, quiet=True)
if not res.get('ok'):
    log = (a.out / 'build.log').read_text() if (a.out / 'build.log').exists() else ''
    errs = [l for l in log.splitlines() if l.startswith('error') or '-->' in l][:12]
    print(json.dumps({'ok': False, 'errors': errs})); sys.exit(1)
d = a.work / 'target-identity/sbpf-solana-solana/release/deps'
for ext in ('ll', 'mir'):
    p = d / f'pump_recovered.{ext}'
    if p.exists():
        t = p.read_text()
        if ext == 'll':
            m = re.search(r'\ndefine[^\n]*multi_hop_curve8swap_hop17h[^\n]*\{\n', t)
            if m:
                e = t.find('\n}\n', m.start()); (a.out / 'swap_hop.ll').write_text(t[m.start() + 1:e + 3])
            shutil.copy2(p, a.out / 'module.ll')
        else:
            m = re.search(r'\nfn multi_hop_curve::swap_hop\(', t)
            if m:
                e = t.find('\n}\n', m.start()); (a.out / 'swap_hop.mir').write_text(t[m.start() + 1:e + 3])
        p.unlink()
o = str(a.out)
subprocess.run(['python3', str(H / 'score.py'), o + '/unstripped.so', '--baseline', a.base, '--json', o + '/score.json', '--quiet'], capture_output=True)
for w, sym, f in (('0x5b3b0', 'multi_hop_curve::swap_hop$', 'hop.json'), ('0x22a10', 'admin_cto::execute$', 'cto.json')):
    r = subprocess.run(['python3', str(H / 'target_metric.py'), o + '/unstripped.so', w, '--sym', sym, '--slots', '4000'], capture_output=True, text=True)
    (a.out / f).write_text(r.stdout.splitlines()[0] if r.stdout else '{}')
s = json.load(open(o + '/score.json')); b = json.load(open(a.base))['windows']; w = s['windows']
hx = lambda k: hex(int(k))
def tm(p):
    try: d = json.loads(open(p).read() or '{}')
    except Exception: return {}
    return {k: d.get(k) for k in ('ratio', 'slots_diff', 'cand_bytes', 'first_diff_offsets')}
r = {'ok': True, 'sha': s['summary'].get('candidate_sha256', '')[:16],
     'normalized': sum(1 for x in w.values() if x['normalized']), 'raw': sum(1 for x in w.values() if x['raw']),
     'losses': [hx(k) for k in b if b[k]['normalized'] and not w.get(k, {}).get('normalized')],
     'raw_losses': [hx(k) for k in b if b[k]['raw'] and not w.get(k, {}).get('raw')],
     'gains': [hx(k) for k in w if w[k]['normalized'] and not b.get(k, {}).get('normalized')],
     'raw_gains': [hx(k) for k in w if w[k]['raw'] and not b.get(k, {}).get('raw')],
     'swap_hop': tm(o + '/hop.json'), 'admin_cto': {k: v for k, v in tm(o + '/cto.json').items() if k != 'first_diff_offsets'}, 'out': o}
if r['swap_hop'].get('first_diff_offsets'): r['swap_hop']['first_diff_offsets'] = r['swap_hop']['first_diff_offsets'][:6]
print(json.dumps(r))
