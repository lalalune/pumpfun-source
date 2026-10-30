#!/bin/bash
# ra.sh <m.ll> <out.log>: debug llc regalloc log
DBG=~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc; o=$(mktemp /tmp/raXXXX).o
$DBG -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $1 -filetype=obj -o $o -debug-only=regalloc 2> $2; rm -f $o
