#!/bin/bash
# sscrun.sh <rxdir>: debug llc with stack-slot-coloring debug + MIR before it; writes ssc.log
D=~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc
cd $1 && $D -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections m.ll -filetype=obj -o /dev/null -print-before=stack-slot-coloring -debug-only=stack-slot-coloring 2> ssc.log
