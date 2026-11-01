#!/bin/bash
# meas.sh <name> <genes> <slot>: crate copy + genes + measure.sh + differential; writes res/meas.jsonl
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a16-shim-outlinerepay
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a16-shim-outlinerepay
n=$1; g=$2; s=$3; v=$OUT/var/m_$n; rm -rf $v; mkdir -p $v
rsync -a --exclude target $WT/programs/pump/ $v/
python3 $OUT/tools/g16.py $v/src/creator/admin_cto.rs "$g" || exit 1
r=$(/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/measure.sh $v $OUT/work$s $OUT/t/$n 2>&1 | tail -1)
echo "$r" > $OUT/t/$n/measure.json
d=$(cd $WT && python3 scripts/pump_admin_cto_differential.py --candidate $OUT/t/$n/candidate.so --output $OUT/t/$n/diff.json 2>&1 | tail -3 | tr '\n' ' ')
python3 - "$n" "$OUT/t/$n" <<'PY'
import json,sys
n,d=sys.argv[1],sys.argv[2]
r=json.load(open(d+'/measure.json'))
try: df=json.load(open(d+'/diff.json'))
except Exception as e: df={'err':str(e)}
c=r.get('admin_cto',{})
o={'name':n,'ok':r.get('ok'),'normalized':r.get('normalized'),'raw':r.get('raw'),'losses':r.get('losses'),'raw_losses':r.get('raw_losses'),'ratio':c.get('ratio'),'slots':c.get('slots_diff'),'bytes':c.get('cand_bytes'),'sha':r.get('sha'),
   'diff':{'cases':df.get('case_count'),'mismatches':len(df.get('mismatches') or []) if 'mismatches' in df else df.get('err')}}
o['losses']=len(o['losses'] or []); o['raw_losses']=len(o['raw_losses'] or [])
print(json.dumps(o))
open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a16-shim-outlinerepay/res/meas.jsonl','a').write(json.dumps(o)+'\n')
PY
rm -rf $v
