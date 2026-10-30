#!/bin/bash
# ctrial.sh <trial> <patch.py> <slot> : copy base src, apply patch.py (edits src dir), capture build+IR, score, metric
T=$1; P=$2; SLOT=${3:-a}
TOOLS=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w4-v3costs
O=$HOME/.cache/pumpfun-reconstruction/lanes/w4-v3costs
B=/private/tmp/claude-501/-Users-shawwalters-Documents-Codex-2026-10-24-pumpfun-source/4381c718-211a-406c-9278-6119c4649998/scratchpad/w3/final/out
S=$O/src/$T; rm -rf $S; mkdir -p $S; rsync -a --exclude target $WT/programs/pump/ $S/
python3 $P $S || { echo PATCH-FAILED; exit 1; }
diff -ru $WT/programs/pump/src $S/src > $O/src/$T.diff
export PUMP_BUILD_SLOTS=10
D=$O/out/$T; rm -rf $D; mkdir -p $D
python3 $O/bin/capture_full.py $S $O/work-$SLOT $D > $D/build.log 2>&1
if [ ! -f $D/unstripped.so ]; then echo "$T BUILD-FAILED"; grep -m5 -A5 '^error' $D/build.log $O/work-$SLOT -r 2>/dev/null | head -20; exit 1; fi
python3 $TOOLS/harness/score.py $D/unstripped.so --baseline $B/score.json --json $D/score.json --quiet >/dev/null
python3 $TOOLS/harness/target_metric.py $D/unstripped.so 0x80df8 --sym 'v3_buy_costs$' > $D/metric.json
python3 $TOOLS/harness/win.py show 0x80df8 --cand $D/unstripped.so --sym 'v3_buy_costs$' --full > $D/diff.txt 2>&1
python3 - $D $O <<'PY'
import json,sys,re
D,O=sys.argv[1:]
s=json.load(open(D+'/score.json'))['summary']; m=json.load(open(D+'/metric.json'))
diff=open(D+'/diff.txt').read().splitlines()
t=open(D+'/pump_recovered.ll').read()
f=re.search(r'^define[^\n]*12v3_buy_costs[^\n]*\{\n.*?^\}\n',t,re.M|re.S)
f=f.group(0) if f else ''
b=open(O+'/ir/base/pump_recovered.ll').read(); fb=re.search(r'^define[^\n]*12v3_buy_costs[^\n]*\{\n.*?^\}\n',b,re.M|re.S).group(0)
norm=lambda x: re.sub(r'h[0-9a-f]{16}E','H',re.sub(r'![0-9]+','!N',x))
print(json.dumps({'trial':D.split('/')[-1],'norm':s['normalized'],'raw':s['raw'],'gains':s['gains']+s['raw_gains'],'losses':s['losses']+s['raw_losses'],'bytes':m['cand_bytes'],'ratio':m['ratio'],'calls':m['calls_candidate'][0],'minus':sum(1 for l in diff if l.startswith('- ')),'plus':sum(1 for l in diff if l.startswith('+ ')),'prof':f.count('!prof'),'ir_same':norm(f)==norm(fb),'sha':s['candidate_sha256'][:16]}))
PY
