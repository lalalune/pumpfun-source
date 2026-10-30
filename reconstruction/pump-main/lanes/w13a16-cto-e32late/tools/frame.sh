#!/bin/bash
# frame.sh <m.ll> -> execute's frame objects (offset size align name)
SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin
T=$(mktemp -d)
$SDK/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections -stop-after=prologepilog $1 -o $T/f.mir 2>/dev/null
python3 /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a16-cto-e32late/tools/mirframe.py $T/f.mir
rm -rf $T
