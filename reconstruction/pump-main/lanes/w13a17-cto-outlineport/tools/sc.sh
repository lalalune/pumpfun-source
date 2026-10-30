#!/bin/bash
# sc.sh <xdir> : stack-coloring groups of execute -> <xdir>/scg.txt
DL=~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc
$DL -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $1/ex.bc -filetype=obj -o /dev/null -debug-only=stack-coloring 2> $1/sc.log
python3 $(dirname "$0")/scg.py $1/sc.log > $1/scg.txt; rm $1/sc.log
