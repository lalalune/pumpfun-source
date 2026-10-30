#!/bin/bash
# kscore.sh <name> <llc opts...> : llc cap/opt.bc with opts, relink, score vs llc-base (if exists) else base
N=$1; shift
L=~/.cache/pumpfun-reconstruction/lanes/w8-profile-flags; R=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)/reconstruction
HL=~/.cache/pumpfun-reconstruction/toolchains/hybrid144/rust/lib/rustlib/aarch64-apple-darwin/bin/llc
D=$L/k/$N; mkdir -p $D
$HL -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections -data-sections -filetype=obj "$@" ${BC:-$L/cap/opt.bc} -o $D/main.o 2>$D/llc.err || { echo "$N LLC-ERR $(head -c 150 $D/llc.err)"; exit 1; }
"$(dirname "$0")/relink.sh" $D/main.o $D/unstripped.so 2>$D/link.err || { echo "$N LINK-ERR"; exit 1; }
B=$L/k/llcbase/score.json; [ -f $B ] || B=$L/out/base/score.json
python3 $R/harness/score.py $D/unstripped.so --baseline $B --json $D/score.json --quiet > /dev/null 2>&1
python3 - $D/score.json $N <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))['summary']
print(sys.argv[2],'norm',d['normalized'],'raw',d['raw'],'gains',d['gains'],'losses',d['losses'][:8],len(d['losses']),'rawg',len(d['raw_gains']),'rawl',len(d['raw_losses']))
PY
python3 $R/harness/target_metric.py $D/unstripped.so 0x80df8 0x1e7c0 0x22a10 0x5b3b0 0x72810 0x13b9b8 0x13f630 0x1489f8 --top 1 2>/dev/null | python3 -c '
import sys,json
print("  "+" ".join("%s:%s/%s%s"%(d["window"][2:],d["cand_bytes"],d["ratio"],(":sd%d"%d["slots_diff"]) if "slots_diff" in d else "") for d in map(json.loads,sys.stdin)))'
rm -f $D/main.o
