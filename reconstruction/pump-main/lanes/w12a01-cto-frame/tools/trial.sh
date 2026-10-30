#!/bin/bash
# trial.sh <name> <workN> [mir]: capture IR of $OUT/var/<name>, run frameoracle (no partition) + target metric, print summary
set -u
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w12a01-cto-frame
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
WT=$(cd "$SCRIPT_DIR/../../../../.." && pwd)
n=$1; w=$2; D=$OUT/t/$n; mkdir -p $D
export PUMP_BUILD_SLOTS=10
if [ "${3:-}" = mir ]; then export EMIT=link,llvm-ir,mir; fi
python3 "$SCRIPT_DIR/capture.py" "$OUT/var/$n" "$OUT/$w" "$D" > "$D/cap.json" 2> "$D/cap.err"
if ! grep -q '"ok": true' $D/cap.json; then echo "$n BUILD FAIL"; tail -c 1500 $D/cap.err; cat $D/cap.json; exit 1; fi
python3 $WT/reconstruction/pump-main/lanes/w4-frame-oracle/frameoracle.py --ir $D/pump_recovered.ll --sym '_ZN14pump_recovered9admin_cto7execute17h[0-9a-f]+E' --win 0x22a10 --name fo --out $D --no-partition --json $D/fo.json > $D/fo.txt 2>&1
python3 $WT/reconstruction/harness/target_metric.py $D/unstripped.so 0x22a10 --sym 'admin_cto::execute$' --slots 4000 2>/dev/null | head -1 > $D/cto.json
python3 - $D <<'PY'
import json,sys,re
d=sys.argv[1]
c=json.loads(open(d+'/cto.json').read() or '{}')
fo=open(d+'/fo.txt').read().splitlines()
ab=[l for l in fo if l.startswith('cand bytes')]
br=[l.strip() for l in fo[fo.index('# delta breaks (orig has DIFF more bytes between A and B):')+1:] if l.strip().startswith(('+','-'))] if '# delta breaks (orig has DIFF more bytes between A and B):' in fo else []
print(json.dumps({'name':d.split('/')[-1],'ratio':c.get('ratio'),'slots':c.get('slots_diff'),'bytes':c.get('cand_bytes'),'calls':c.get('calls_candidate'),'fo':ab[0] if ab else None,'breaks':br[:4]}))
PY
rm -f $D/candidate.so $D/link.map
