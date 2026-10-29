#!/bin/zsh
# trial.sh <name> : build current worktree, score, metric
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w3-adminCTO
OUT=~/.cache/pumpfun-reconstruction/lanes/w3-adminCTO
T=$WT/reconstruction/harness
B=/private/tmp/claude-501/-Users-shawwalters-Documents-Codex-2026-10-24-pumpfun-source/4381c718-211a-406c-9278-6119c4649998/scratchpad/w3/base/out
export PUMP_BUILD_SLOTS=10
n=$1; W=${2:-work}
python3 $T/fastbuild.py --src $WT/programs/pump --work $OUT/$W --out $OUT/out/$n > $OUT/out/$n.log 2>&1 || { tail -30 $OUT/out/$n.log; exit 1; }
python3 $T/score.py $OUT/out/$n/unstripped.so --baseline $B/score.json --json $OUT/out/$n/score.json --quiet | tail -1
python3 $T/target_metric.py $OUT/out/$n/unstripped.so 0x22a10 --sym 'admin_cto.*execute'
python3 $OUT/scripts/cand.py $OUT/out/$n/unstripped.so > $OUT/$n.txt
python3 $OUT/scripts/offs.py $OUT/$n.txt | python3 -c "
import sys,re
t=sys.stdin.read(); v=[int(x,16) for x in re.findall(r' ([0-9a-f]+):',t)]; print('max r10 off',hex(max(v)), 'distinct',len(v))"
