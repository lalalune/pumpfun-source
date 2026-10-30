#!/bin/sh
# build.sh <name> [ir]: fastbuild OUT/src/<name> (or capture IR), score, target metric
L=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w6r1-execute-ir; T=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r1-execute-ir/reconstruction/harness
B=/private/tmp/claude-501/-Users-shawwalters-Documents-Codex-2026-10-24-pumpfun-source/9ebf44b6-961d-4889-839c-f928372efc77/scratchpad/w6/base/score.json
export PUMP_BUILD_SLOTS=10; n=$1
if [ "$2" = ir ]; then python3 $L/scripts/capmir.py $L/src/$n $L/work-$n $L/out/$n > $L/out/$n.log 2>&1
else python3 $T/fastbuild.py --src $L/src/$n --work $L/work-$n --out $L/out/$n > $L/out/$n.log 2>&1; fi
rm -rf $L/work-$n
[ -f $L/out/$n/unstripped.so ] || { echo "$n BUILD FAIL"; grep -m3 'error' $L/out/$n.log; exit 1; }
python3 $T/score.py $L/out/$n/unstripped.so --baseline $B --json $L/out/$n/score.json --quiet >/dev/null 2>&1
python3 -c "import json;d=json.load(open('$L/out/$n/score.json'))['summary'];print('$n',d['normalized'],d['raw'],'gains',d['gains'],'losses',d['losses'],'rawgain',d['raw_gains'],'rawloss',d['raw_losses'],d['candidate_sha256'][:8])"
python3 $T/target_metric.py $L/out/$n/unstripped.so 0x1e7c0 --sym 'create_v2.*execute' | python3 -c "import json,sys;d=json.loads(sys.stdin.read());print('$n','ratio',d['ratio'],'bytes',d['cand_bytes'],'calls',d.get('calls_candidate'),'slots',d.get('slots_diff'))"
