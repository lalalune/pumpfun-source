#!/bin/bash
# trial.sh name edit.py [worktag] [extra-rustc-flags] -> copy crate, apply edit(text) to multi_hop_curve_swap.rs, build w/ IR, oracle metrics
set -e
n=$1; ed=$2; tag=${3:-a}; extra=${4:-}
OUT=~/.cache/pumpfun-reconstruction/lanes/w12b05-hop-irshape; WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w12b05-hop-irshape
SRC=${SRC:-$WT/programs/pump}
export PUMP_BUILD_SLOTS=10
rm -rf $OUT/var/$n; mkdir -p $OUT/var/$n; rsync -a --exclude target $SRC/ $OUT/var/$n/src/
python3 - "$OUT/var/$n/src/src/multi_hop_curve_swap.rs" "$ed" <<'P'
import sys,runpy
p=sys.argv[1]; t=open(p).read(); n0=t.count('\n'); t2=runpy.run_path(sys.argv[2])['edit'](t)
assert t2!=t, 'edit no-op'
assert t2.count('\n')==n0, 'line count changed %d->%d'%(n0,t2.count('\n'))
open(p,'w').write(t2)
P
python3 $OUT/tools/capir.py --src $OUT/var/$n/src --work $OUT/work_$tag --out $OUT/var/$n/out --extra "$extra" > $OUT/var/$n/build.txt 2>&1 || { grep -E "^error|-->" $OUT/var/$n/out/build.log 2>/dev/null | head; tail -5 $OUT/var/$n/build.txt; exit 1; }
python3 $WT/reconstruction/harness/target_metric.py $OUT/var/$n/out/unstripped.so 0x5b3b0 --sym 'multi_hop_curve::swap_hop$' --slots 4000 | head -1 > $OUT/var/$n/hop.json
python3 -c "import json; d=json.load(open('$OUT/var/$n/hop.json')); print('$n', d['cand_bytes'], d['ratio'], d['slots_diff'], d['calls_candidate'])"
