#!/bin/bash
# mkdbg.sh <m.ll|.mir> <dir> [extra llc args for the .mir start]: pre.mir / ssc.mir / ssc.log for mirperm.py
SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin; DBG=~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc
A=(-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections)
I=$1; D=$2; shift 2; mkdir -p $D
printf '#!/bin/bash\nexec %s/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections "$@"\n' $SDK > $D/llc.sh; chmod +x $D/llc.sh
$SDK/llc "${A[@]}" $I "$@" -stop-before=stack-slot-coloring -o $D/pre.mir || exit 1
$SDK/llc "${A[@]}" $I "$@" -stop-after=stack-slot-coloring -o $D/ssc.mir || exit 1
$DBG "${A[@]}" $I "$@" -stop-after=stack-slot-coloring -o /dev/null -debug-only=stack-slot-coloring 2> $D/ssc.log
$SDK/llc "${A[@]}" $D/ssc.mir -start-after=stack-slot-coloring -filetype=obj -o $D/rt.o
