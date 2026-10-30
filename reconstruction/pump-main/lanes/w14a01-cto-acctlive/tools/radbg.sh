#!/bin/bash
# radbg.sh <dir>: debug-regalloc log of <dir>/m.ll into <dir>/ra.log, split MIR (mi0) and coalescer (coal) sections
D=~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc
cd $1 && $D -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections m.ll -filetype=obj -o /dev/null -debug-only=regalloc 2> ra.log
a=$(grep -n "^\*\*\*\*\*\*\*\*\*\* MACHINEINSTRS" ra.log | head -1 | cut -d: -f1); b=$(grep -n "^\*\*\*\*\*\*\*\*\*\* REGISTER COALESCER" ra.log | head -1 | cut -d: -f1); c=$(grep -n "^\*\*\*\*\*\*\*\*\*\* GREEDY" ra.log | head -1 | cut -d: -f1)
sed -n "${a},${b}p" ra.log > mi0.txt; sed -n "${b},${c}p" ra.log > coal.txt
