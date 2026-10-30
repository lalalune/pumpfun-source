#!/bin/bash
# trial.sh TAG: capture build of this worktree, SROA phi order at execute's post-inline SROA, score, target metric.
set -e
L=x1-sroa-debug-requeue-trace; C=$HOME/.cache/pumpfun-reconstruction/lanes/$L; W=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/$L
B=$HOME/.cache/pumpfun-reconstruction/llvm-dbg/build/bin; T=$1; O=$C/cap-$T
export CARGO_BUILD_JOBS=3
cd $W
nice -n 10 python3 reconstruction/pump-main/lanes/$L/scripts/capture.py $W/programs/pump $O | tail -1
FN=_ZN14pump_recovered9create_v27execute17h3f7d08900031c023E
$B/llvm-extract -S --func=$FN $O/m1.ll -o $O/x1.ll 2>/dev/null && $B/opt -S -passes='function(sroa<modify-cfg>)' $O/x1.ll -o $O/xo1.ll -debug-only=sroa 2> $O/sroa-dbg.txt && python3 - $O/xo1.ll <<'PY' || true
import re,sys
o=open(sys.argv[1]).read()
for m in re.finditer(r'\n([\w.$"]+):[^\n]*\n((?:  %[^\n]*= phi[^\n]*\n)+)',o):
    names=re.findall(r'  %(\.sroa\.\d+)[\w.]* = phi',m.group(2))
    if len(names)>=4: print('phis',m.group(1)[:30]+': '+','.join(n.split('.')[-1] for n in names))
PY
rm -f $O/m0.ll $O/m2.ll $O/m3.ll
python3 reconstruction/harness/score.py $O/unstripped.so --baseline /Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/x-baseline/1852a872e/score.json --json $O/score.json >/dev/null 2>&1 || true
python3 -c "import json;d=json.load(open('$O/score.json'))['summary'];print('score',d['normalized'],d['raw'],'losses',d['losses'],'raw_losses',d['raw_losses'],'gains',d['gains'])"
python3 reconstruction/harness/target_metric.py $O/unstripped.so 0x1e7c0 | head -1 | python3 -c "import sys,json;d=json.loads(sys.stdin.read());print('tm',d['cand_bytes'],d['ratio'],d.get('slots_diff'),d.get('first_diff_offsets'))"
shasum -a256 $O/unstripped.so | cut -c1-12
