#!/usr/bin/env python3
"""multisink.py <mod.ll> <outdir> <label>=<v1,v2..> ...: llc oracle for several values sunk to their use block at once
(edit_sink1 semantics), printing ratio/abs/bytes and clonefeat spill/reg."""
import sys, os, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ctoracle as co, clonefeat as cf
mod, out = sys.argv[1], sys.argv[2]
for spec in sys.argv[3:]:
    lab, vs = spec.split('=')
    env = dict(os.environ, SINK=vs)
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ctoracle.py'), 'run', mod, out + '/' + lab,
                        '--edit', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edit_sink1.py')], env=env, capture_output=True, text=True)
    m = json.loads(r.stdout.strip().split('\n')[-1]) if r.returncode == 0 else {'err': r.stderr[-300:]}
    if 'ratio' in m:
        b = open(out + '/' + lab + '/fn.bin', 'rb').read(); toks = [b[i:i+8] for i in range(0, len(b), 8)]
        # fn.bin keeps lddw as 16 B tokens? fall back: clonefeat only needs 8 B ldx tokens
        m['cf'] = cf.feats(toks)
    print(lab, json.dumps(m))
