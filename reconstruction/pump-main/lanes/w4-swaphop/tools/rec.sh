#!/bin/bash
# rec.sh trial mechanism status "hypothesis" "notes"
O=~/.cache/pumpfun-reconstruction/lanes/w4-swaphop; W=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w4-swaphop
L=$W/reconstruction/pump-main/log_attempt.py
T=$1; K=0x5b3b0-main-630a074-$2-v1
python3 $L check --dedupe-key $K | grep -q '"duplicate": true' && { echo DUP $K; }
DATA=$(python3 - "$T" "$5" <<'PY'
import json,sys,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w4-swaphop'); t=sys.argv[1]
L=open(f'{O}/out-{t}.txt').read().split('\n') if os.path.exists(f'{O}/out-{t}.txt') else []
try:
  s=json.loads(L[0]); m=json.loads(L[1])
  seg=[l for l in L if l.startswith('calls ')][-1]; bx=[l for l in L if l.startswith('bytes ')][-1]
  d={"output":f"{O}/out/{t}","normalized":s['normalized'],"raw":s['raw'],"gains":s['gains'],"losses":s['losses'],"raw_losses":s['raw_losses'],
   "target":{"ratio":m['ratio'],"cand_bytes":m['cand_bytes'],"seg":seg,"metrics":bx},"notes":sys.argv[2]}
except Exception as e: d={"output":f"{O}/out/{t}","notes":sys.argv[2]}
print(json.dumps(d))
PY
)
python3 $L record --lane w4-swaphop --approach stack-frame-layout --target 0x5b3b0 --dedupe-key $K --hypothesis "$4" --status $3 --data "$DATA" | tail -1
