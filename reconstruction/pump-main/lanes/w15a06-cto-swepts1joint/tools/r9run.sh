#!/bin/bash
# r9run.sh <m.ll> <dir> <vreg|auto> <Jbb|auto> [reg]: pre-greedy MIR round trip (rt) and swept->$reg pin (r9); writes rt.o r9.o pre.mir pre_r9.mir
SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin; A=(-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections)
T=$(dirname $0); I=$1; D=$2; V=$3; J=$4; R=${5:-r9}; mkdir -p $D
$SDK/llc "${A[@]}" $I -stop-before=register-coalescer -o $D/pre.mir || exit 1
$SDK/llc "${A[@]}" $D/pre.mir -start-before=register-coalescer -filetype=obj -o $D/rt.o || exit 1
[ "$V" = auto ] && read V J < <(python3 $T/swfind.py $D/pre.mir)
python3 $T/swr9.py $D/pre.mir $D/pre_r9.mir $V $J $R || exit 1
$SDK/llc "${A[@]}" $D/pre_r9.mir -start-before=register-coalescer -filetype=obj -o $D/r9.o || exit 1
