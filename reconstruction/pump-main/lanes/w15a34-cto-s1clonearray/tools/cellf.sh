#!/bin/bash
# cellf.sh <m.ll> <dir>: free cell only (private llc, RAPRIO_* env honoured): "free: ratio R M m bytes b"
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a18-cto-s1greedy; L=$O/llvmb/bin/llc; W=$O/w6
I=$1; D=$2; mkdir -p $D
$L -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $I -filetype=obj -o $D/rt.o || exit 1
F=$(python3 $W/tools/objsc.py $D/rt.o | sed 's/^[^ ]* *//')
echo "free: $F"
