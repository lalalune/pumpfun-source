#!/bin/bash
# bld.sh <NN> [crate dir]: build the crate (default lanes/integ-layout/src) into builds/bNN (src snapshot kept), then score
# vs round37 (official baseline -> score.json) and vs the r37g5 genuine base (-> score_vs_base.json).
W=/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work
L=$W/lanes/integ-layout
N=$1; SRC=${2:-$L/src}; O=$L/builds/b$N
BASESCORE=${BASESCORE:-$W/integ/r37g5/score.json}
rm -rf $O; mkdir -p $O
cp -R $SRC $O/src
python3 $W/harness/fastbuild.py --src $O/src --work $L/work --out $O > $O/fastbuild.out 2>&1
python3 - "$O" <<'PY'
import json,sys
from pathlib import Path
o=Path(sys.argv[1]); t=(o/'fastbuild.out').read_text()
i=t.rfind('\n{'); i = 0 if t.startswith('{') and i<0 else i+1
try: d=json.loads(t[i:t.rindex('}')+1])
except Exception as e: d={'ok':False,'raw':t[-3000:],'err':str(e)}
(o/'fastbuild.json').write_text(json.dumps(d,indent=1))
print('build', {k:d.get(k) for k in ('ok','runtime_valid','stack_warnings','seconds','unstripped_sha256')})
PY
if [ -f $O/unstripped.so ]; then
  python3 $W/harness/score.py $O/unstripped.so --baseline $W/base/round37/inventory.json --json $O/score.json --quiet > /dev/null
  python3 $W/harness/score.py $O/unstripped.so --baseline $BASESCORE --json $O/score_vs_base.json --quiet > /dev/null
  python3 - "$O" <<'PY'
import json,sys
o=sys.argv[1]
a=json.load(open(o+'/score.json'))['summary']; b=json.load(open(o+'/score_vs_base.json'))['summary']
print(f"score: {a['normalized']} normalized / {a['raw']} raw; vs round37 +{len(a['gains'])} -{len(a['losses'])} (raw -{len(a['raw_losses'])}); "
      f"vs base: gains {b['gains']} losses {b['losses']} raw_losses {b['raw_losses']}")
PY
fi
