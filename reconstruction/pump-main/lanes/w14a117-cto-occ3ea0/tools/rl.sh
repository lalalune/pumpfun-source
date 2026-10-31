#!/bin/bash
# rl.sh <m.ll|m.mir> <out> [extra llc args]: private patched llc (RAPRIO_* env honoured)
O=~/.cache/pumpfun-reconstruction/lanes/w14a117-cto-occ3ea0
in=$1; out=$2; shift 2
exec $O/llvmb/bin/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections "$in" -filetype=obj -o "$out" "$@"
