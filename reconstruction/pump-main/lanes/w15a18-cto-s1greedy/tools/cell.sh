#!/bin/bash
# cell.sh <m.ll> <dir>: private-llc (RAPRIO_* env honoured) free / pinV / pinA cells. Prints "free M.. pinV M.. pinA M.."
O=~/.cache/pumpfun-reconstruction/lanes/w15a18-cto-s1greedy; L=$O/llvmb/bin/llc; W=$O/w6
A=(-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections)
I=$1; D=$2; mkdir -p $D
printf '#!/bin/bash\nexec %s -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections "$@"\n' $L > $D/llc.sh; chmod +x $D/llc.sh
$L "${A[@]}" $I -stop-before=stack-slot-coloring -o $D/pre.mir || exit 1
$L "${A[@]}" $I -stop-after=stack-slot-coloring -o $D/ssc.mir -debug-only=stack-slot-coloring 2> $D/ssc.log || exit 1
unset RAPRIO_LOG
$L "${A[@]}" $D/ssc.mir -start-after=stack-slot-coloring -filetype=obj -o $D/rt.o || exit 1
F=$(python3 $W/tools/objsc.py $D/rt.o | sed 's/^[^ ]* *//')
PV=$(python3 $W/t139/mirperm.py $D valid 2>/dev/null)
PA=$(python3 $W/t139/mirperm.py $D all 2>/dev/null)
echo "free: $F | pinV: $PV | pinA: $PA"
