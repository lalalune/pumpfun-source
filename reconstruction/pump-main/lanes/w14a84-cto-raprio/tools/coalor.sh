#!/bin/bash
# coalor.sh <m.ll> <name>: "ideal coalescer order" MIR oracle: merge swept's coalescing class into the Err-payload class
# before RegisterCoalescer (no CFG change), then finish llc and score (experiment only).
D=~/.cache/pumpfun-reconstruction/lanes/w14a84-cto-raprio; T=$D/tools; N=$2; mkdir -p $D/mir
SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin; DBG=~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc
A=(-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections)
$DBG "${A[@]}" "$1" -filetype=obj -o $D/mir/$N.dbg.o -debug-only=regalloc 2> $D/mir/$N.ra.log
C=$(python3 $T/coal.py "$1" 2>/dev/null | sed 's/.*: //'); PAY=$(echo "$C" | grep -o 'pay=%[0-9]*' | cut -d= -f2); SW=$(echo "$C" | grep -o 'swept_vreg=%[0-9]*' | cut -d= -f2)
$SDK/llc "${A[@]}" "$1" -stop-before=register-coalescer -o $D/mir/$N.mir
python3 $T/mirren.py $D/mir/$N.mir $D/mir/$N.c.mir $PAY $(python3 $T/ufclass.py $D/mir/$N.ra.log $SW)
$SDK/llc "${A[@]}" $D/mir/$N.c.mir -start-before=register-coalescer -filetype=obj -o $D/mir/$N.c.o
echo "$N base: $C"; echo -n "$N coal-order: "; python3 $T/objscore.py $D/mir/$N.c.o
rm -f $D/mir/$N.dbg.o $D/mir/$N.ra.log
