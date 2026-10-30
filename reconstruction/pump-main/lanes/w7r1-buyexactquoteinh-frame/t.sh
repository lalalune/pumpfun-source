#!/bin/bash
# t.sh <name> [base]: gen src/<name> from spec/<name>.py on src/<base|base>, build with work dir work<WS>, metric + score
source ~/.cache/pumpfun-reconstruction/lanes/w7r1-buyexactquoteinh-frame/env.sh
n=$1; b=${2:-base}
python3 $OUT/scripts/gen.py $b $n $OUT/spec/$n.py || exit 1
python3 $H/fastbuild.py --src $OUT/src/$n --work $OUT/work$WS --out $OUT/out/$n > $OUT/out/$n.log 2>&1 || { echo "BUILD FAIL $n"; grep -m5 "^error" -A8 $OUT/out/$n/build.log; exit 1; }
python3 $H/target_metric.py $OUT/out/$n/unstripped.so 0x13f630 --sym 'buy_exact_quote_in_handler$' --top 1 | python3 -c "import json,sys;d=json.loads(sys.stdin.readline());print('$n','bytes',d['cand_bytes'],'ratio',d['ratio'],'slots',d.get('slots_diff'),'calls',d['calls_candidate'])"
python3 $H/target_metric.py $OUT/out/$n/unstripped.so 0x13b9b8 --sym 'buy_v2::buy_handler$' --top 1 | python3 -c "import json,sys;d=json.loads(sys.stdin.readline());print('  buy_handler','bytes',d['cand_bytes'],'ratio',d['ratio'],'slots',d.get('slots_diff'))"
python3 $H/score.py $OUT/out/$n/unstripped.so --baseline $OUT/out/base/score.json --json $OUT/out/$n/score.json --quiet | python3 -c "import json,sys;d=json.load(sys.stdin);print('  score',d['normalized'],d['raw'],'G',d['gains'],'L',d['losses'],'RG',d['raw_gains'],'RL',d['raw_losses'])"
python3 $H/win.py show 0x13f630 --cand $OUT/out/$n/unstripped.so --sym 'buy_exact_quote_in_handler$' > $OUT/out/$n.diff 2>&1
