#!/bin/zsh
# irtrial.sh <name>: capture IR of current worktree source, dump execute frame objects
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w3-adminCTO
OUT=~/.cache/pumpfun-reconstruction/lanes/w3-adminCTO
SDK=~/.cache/solana/v1.44/platform-tools
export PUMP_BUILD_SLOTS=10
n=$1; D=$OUT/out/ir-$n
rsync -a --delete $WT/programs/pump/ $OUT/src/ir/
python3 $OUT/scripts/capture2.py $OUT/src/ir $OUT/work-ir $D > $D.log 2>&1 || { tail -20 $D.log; exit 1; }
SYM=$(grep -o '_ZN14pump_recovered9admin_cto7execute17h[0-9a-f]*E' $D/pump_recovered.ll | head -1)
awk -v s="$SYM" 'index($0,"define")==1 && index($0,s){f=1} f{print} f && /^}/{exit}' $D/pump_recovered.ll > $D/execute.ll
$SDK/llvm/bin/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext $D/pump_recovered.ll -filetype=obj -o $D/llc.o -print-after=prologepilog -filter-print-funcs=$SYM 2> $D/pei.txt
python3 $OUT/scripts/allocas.py $D/execute.ll > $D/allocas.txt
python3 $OUT/scripts/frame.py $D
