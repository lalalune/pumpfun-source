#!/bin/bash
# iro.sh <base m.ll> <name> moves... : post-opt IR block moves -> llc -> sc.py (ratio bytes M jM ...)
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a134-cto-headroute306
SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin
b=$1; n=$2; shift 2
python3 $O/tools/mv2.py $b $O/io/$n.ll "$@" || exit 1
$SDK/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $O/io/$n.ll -filetype=obj -o $O/io/$n.o || exit 1
echo "$n [$*] $(python3 $O/tools/sc.py $O/io/$n.o | cut -d' ' -f2-)"
rm -f $O/io/$n.ll
