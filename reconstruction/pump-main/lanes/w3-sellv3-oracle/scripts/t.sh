#!/bin/bash
# t.sh <trial> <edits.py> [cap]  : make variant, build (fastbuild), score, metric; cap=1 also captures IR + oracle compare
export PUMP_BUILD_SLOTS=10
O=~/.cache/pumpfun-reconstruction/lanes/w3-sellv3-oracle
TOOLS=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w3-sellv3-oracle/reconstruction
BASEJ=/private/tmp/claude-501/-Users-shawwalters-Documents-Codex-2026-10-24-pumpfun-source/4381c718-211a-406c-9278-6119c4649998/scratchpad/w3/base/out/score.json
T=$1; E=$2
python3 $O/tools/mkvar.py $T $E >/dev/null || exit 1
S=$O/src/$T
cd /tmp
if [ "$3" = cap ]; then
  python3 $O/tools/capture_ir.py $S $O/out/$T $O/work-ir-$T > $O/out/$T.build.log 2>&1 || { echo BUILD-FAIL; grep -m5 -A7 '^error' $O/out/$T.build.log; exit 1; }
  python3 $O/tools/slim.py $O/out/$T/module.ll 5trade4sell17h $O/out/$T/slim.ll
  rm -f $O/out/$T/module.ll; rm -rf $O/work-ir-$T
  ORIG=$O/oracle/orig.sell.txt TAG=$T python3 $O/tools/oracle.py $O/out/$T/slim.ll 5trade4sell17h
else
  python3 $TOOLS/harness/fastbuild.py --src $S --work $O/work-${W:-a} --out $O/out/$T > $O/out/$T.build.log 2>&1 || { echo BUILD-FAIL; grep -m5 -A7 '^error' $O/out/$T.build.log; exit 1; }
fi
python3 $TOOLS/harness/score.py $O/out/$T/unstripped.so --baseline $BASEJ --json $O/out/$T/score.json --quiet | python3 -c "import json,sys;d=json.load(sys.stdin);print('SCORE',d['normalized'],d['raw'],d['gains'],d['losses'],d['raw_gains'],d['raw_losses'],d['candidate_sha256'][:12])"
python3 $TOOLS/harness/target_metric.py $O/out/$T/unstripped.so 0x14a8a8 --sym 'trade::sell$' | python3 -c "import json,sys;d=json.loads(sys.stdin.readline());print(d['window'],d['cand_bytes'],'/',d['window_bytes'],d['ratio'],d.get('slots_diff',''),d['calls_candidate'],d['normalized_equal'])"
