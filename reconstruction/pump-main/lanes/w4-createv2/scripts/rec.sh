#!/bin/sh
# rec.sh <key-suffix> <status> <hypothesis> <notes> [trialname]
L=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/pump-main/log_attempt.py
K="0x1e7c0-main-630a074-$1-v1"
python3 $L check --dedupe-key "$K" >/dev/null 2>&1 || true
D="{\"notes\":\"$4\"}"
if [ -n "$5" ] && [ -f ~/.cache/pumpfun-reconstruction/lanes/w4-createv2/out/$5/score.json ]; then
D=$(python3 - "$5" "$4" <<'P'
import json,sys,subprocess,os
n=sys.argv[1];O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w4-createv2')
s=json.load(open(f'{O}/out/{n}/score.json'))['summary']
t=json.loads(subprocess.check_output(['python3','/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/harness/target_metric.py',f'{O}/out/{n}/unstripped.so','0x1e7c0','--sym','create_v2.*execute']))
print(json.dumps({"output":f'{O}/out/{n}',"normalized":s['normalized'],"raw":s['raw'],"gains":s['gains'],"losses":s['losses'],"raw_losses":s['raw_losses'],"sha":s['candidate_sha256'][:12],"target":{"slots_diff":t.get('slots_diff'),"ratio":t['ratio'],"cand_bytes":t['cand_bytes']},"notes":sys.argv[2]}))
P
)
fi
python3 $L record --lane w4-createv2 --approach ir-oracle --target 0x1e7c0 --dedupe-key "$K" --hypothesis "$3" --status $2 --data "$D" | tail -1
