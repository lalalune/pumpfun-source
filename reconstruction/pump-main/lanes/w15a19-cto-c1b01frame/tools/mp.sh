#!/bin/bash
# mp.sh <rxname>...: pei.mir via llc -stop-after=prologepilog, f.o copy, then permhc (Mperm + swap climb)
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a19-cto-c1b01frame; SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin
for n in "$@"; do d=$O/rx/$n
 [ -f $d/pei.mir ] || $SDK/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $d/m.ll -stop-after=prologepilog -o $d/pei.mir
 cp -f $d/m.o $d/f.o; python3 $O/t2/permhc.py $d 2>/dev/null; rm -f $d/f.o
done
