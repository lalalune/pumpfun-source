#!/bin/bash
# run.sh SLOT NAME [hunk...]   (base admin_cto.rs from worktree origin/main)
set -u
L=~/.cache/pumpfun-reconstruction/lanes/y1-cto-diffwin
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/y1-cto-diffwin
B=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/y-baseline/0bcf7223c/score.json
SLOT=$1; NAME=$2; shift 2
S=$L/src-$SLOT
(cd $WT && python3 reconstruction/pump-main/log_attempt.py check --dedupe-key 0x22a10-43daa2043-diffwin-$NAME-v1) | grep -q '"duplicate": true' && { echo dup; exit 0; }
mkdir -p $L/res $L/srcs
if [ ! -d $S ]; then cp -R $WT/programs/pump $S; fi
BASE=${BASEFILE:-$L/base_admin_cto.rs}
python3 $L/tools/hunks.py $BASE $S/src/creator/admin_cto.rs "$@" || { echo "{\"name\":\"$NAME\",\"error\":\"apply\"}" > $L/res/$NAME.json; exit 1; }
cp $S/src/creator/admin_cto.rs $L/srcs/$NAME.rs
O=$L/out-$NAME
nice -n 10 env CARGO_BUILD_JOBS=2 python3 $WT/reconstruction/harness/fastbuild.py --src $S --work $L/work-$SLOT --out $O > $O.build.json 2>&1
if [ ! -f $O/unstripped.so ]; then echo "{\"name\":\"$NAME\",\"error\":\"build\"}" > $L/res/$NAME.json; exit 1; fi
python3 $WT/reconstruction/harness/score.py $O/unstripped.so --baseline $B --json $O/score.json > /dev/null
python3 - "$NAME" "$O" "$@" <<'PY' > $L/res/$NAME.json
import json,sys,subprocess
name,o,*h=sys.argv[1:]
s=json.load(open(o+'/score.json'))['summary']
tm=subprocess.run(['python3','/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/y1-cto-diffwin/reconstruction/harness/target_metric.py',o+'/unstripped.so','0x22a10'],capture_output=True,text=True).stdout.splitlines()[0]
t=json.loads(tm)
nf=t.get('normalized_field_differences',{})
print(json.dumps({'name':name,'hunks':h,'bytes':t['cand_bytes'],'ratio':t['ratio'],'calls':t['calls_candidate'],'norm':s['normalized'],'raw':s['raw'],'losses':len(s['losses']),'raw_losses':len(s['raw_losses']),'gains':len(s['gains']),'raw_gains':len(s['raw_gains']),'slots_diff':t.get('slots_diff'),'nfd':{k:v for k,v in nf.items() if not isinstance(v,(list,dict))}}))
PY
cat $L/res/$NAME.json
