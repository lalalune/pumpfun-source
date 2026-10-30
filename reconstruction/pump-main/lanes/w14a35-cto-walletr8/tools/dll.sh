#!/bin/bash
# dll.sh <m.ll> > dis : llc + disassemble execute (function-relative offsets)
SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin; o=$(mktemp /tmp/dllXXXX).o
$SDK/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $1 -filetype=obj -o $o
bash ~/.cache/pumpfun-reconstruction/lanes/w14a35-cto-walletr8/tools/dis.sh $o; rm -f $o
