#!/bin/bash
# promote.sh <trial>: verify a 27,400 B zero-loss trial, run the admin_cto runtime differential, copy its source into the worktree.
set -u
T=$1
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w12a13-cto-sizeknobs
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w12a13-cto-sizeknobs
python3 - "$OUT/res/$T.json" <<'PY' || exit 1
import json,sys
r=json.load(open(sys.argv[1]))
b=json.loads(open('/Users/shawwalters/.cache/pumpfun-reconstruction/w11/current-baseline/cto.json').read())
print('trial', r['name'], r['bytes'], r['ratio'], 'main', b['ratio'], 'losses', r['losses'], r['raw_losses_n'])
ok = r['bytes']==27400 and r['ratio']>b['ratio'] and not r['losses'] and r['raw_losses_n']==0
sys.exit(0 if ok else 1)
PY
[ -f "$OUT/t/$T/candidate.so" ] || { echo "no candidate.so kept for $T"; exit 1; }
cd $WT && python3 scripts/pump_admin_cto_differential.py --candidate "$OUT/t/$T/candidate.so" --output "$OUT/t/$T/diff.json" > "$OUT/t/$T/diff.log" 2>&1; rc=$?
tail -2 "$OUT/t/$T/diff.log"
grep -q "mismatches \[\]" "$OUT/t/$T/diff.log" || { echo "DIFFERENTIAL FAILED rc=$rc"; exit 1; }
cp "$OUT/src/$T.rs" "$WT/programs/pump/src/creator/admin_cto.rs"
git -C $WT diff --stat
