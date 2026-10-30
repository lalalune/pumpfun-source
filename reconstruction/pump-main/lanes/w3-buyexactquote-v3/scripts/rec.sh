#!/bin/bash
# rec.sh <trial> <mech> <status> <hypothesis> [notes]
L=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w3-buyexactquote-v3/reconstruction/pump-main/log_attempt.py
t=$1; m=$2; st=$3; h=$4; n=${5:-}
D=$(python3 - "$t" "$n" <<'PY'
import json,sys,re,os
t,n=sys.argv[1],sys.argv[2]; O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w3-buyexactquote-v3')
s=json.load(open(f'{O}/out/{t}/score.json')) if os.path.exists(f'{O}/out/{t}/score.json') else {}
txt=open(f'{O}/out/{t}.txt').read() if os.path.exists(f'{O}/out/{t}.txt') else ''
m=re.search(r'target bytes (\d+) ratio ([0-9.]+)',txt); d=re.search(r'diffslots=(\d+) ratio',txt); mk=re.search(r'masked: diffslots=(\d+) ratio=([0-9.]+)',txt)
g=re.search(r'norm (\d+) raw (\d+)',txt)
print(json.dumps({"output":f'{O}/out/{t}',"normalized":int(g.group(1)) if g else None,"raw":int(g.group(2)) if g else None,"gains":[],"losses":[] if g and 'losses []' in txt else None,
 "target":{"slots_diff":int(d.group(1)) if d else None,"ratio":float(m.group(2)) if m else None,"cand_bytes":int(m.group(1)) if m else None,"masked_diffslots":int(mk.group(1)) if mk else None,"masked_ratio":float(mk.group(2)) if mk else None},"notes":n}))
PY
)
python3 $L record --lane w3-buyexactquote-v3 --approach semantic-reconstruction --target 0x1489f8 --dedupe-key "0x1489f8-main-6654999-$m-v1" --hypothesis "$h" --status $st --data "$D" | tail -1
