#!/usr/bin/env python3
"""keyscan.py <mod.ll> <outdir> [--pair]: llc oracle for the hand-written AccountInfo clone order
`AccountInfo{lamports:x.lamports.clone(),data:x.data.clone(),key:x.key,..}`: for every inlined AccountInfo::clone
in execute (key load `%_2.iN = load ptr, ptr %X` followed by the lamports Rc at X+8), move the key load to right
before the owner load (X+24), i.e. after both Rc increments. Prints ratio/bytes/clonefeat per clone; the clone is
identified by the struct slot its key is stored to."""
import sys, os, re, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ctoracle as co, clonefeat as cf
mod, out = sys.argv[1], sys.argv[2]
txt = open(mod).read(); sym = co.SYMRE.search(txt).group(0); i, j = co.fn_bounds(txt, sym); L = txt[i:j].split('\n')
moves = []
for k, l in enumerate(L):
    m = re.match(r'  %(_2\.i\d+) = load ptr, ptr %([\w.]+), align 8', l)
    if not m: continue
    key, X = m.group(1), m.group(2)
    # owner load: gep X,24 then load
    g = [n for n in range(k, min(k + 60, len(L))) if re.match(r'  %(\S+) = getelementptr inbounds i8, ptr %' + re.escape(X) + r', i64 24$', L[n])]
    if not g: continue
    gname = re.match(r'  %(\S+) = ', L[g[0]]).group(1)
    st = [x for x in L if re.search(r'store ptr %' + re.escape(key) + r', ptr %(\S+),', x)]
    slot = re.search(r'ptr %(\S+),', st[0].split('store ptr')[1]).group(1) if st else '?'
    moves.append((key, gname, slot))
env0 = dict(os.environ)
res = []
for key, gname, slot in moves:
    env = dict(env0, MOVE=f'{key}@x@before:{gname}')
    r = subprocess.run([sys.executable, os.path.dirname(os.path.abspath(__file__)) + '/ctoracle.py', 'run', mod, f'{out}/{key}', '--edit',
                        os.path.dirname(os.path.abspath(__file__)) + '/edit_move.py'], env=env, capture_output=True, text=True)
    m = json.loads(r.stdout.strip().split('\n')[-1]) if r.returncode == 0 else {'err': r.stderr[-200:]}
    print(key, slot, json.dumps(m), flush=True); res.append((key, slot, m))
