#!/bin/bash
# rst.sh <rx> <refm.ll> <tag>: layout-restore oracle (w16a09 blkrestore.py): re-sort execute blocks of rx/<rx> into the ref layout.
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a13-cto-sutag306; cd $OUT; n=$1; REFLL=$2; TAG=$3
S=~/.cache/solana/v1.44/platform-tools/llvm/bin/llc; A="-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections"
D=$OUT/rst/${n}_$TAG; mkdir -p $D $OUT/rst/ref_$TAG
[ -f $OUT/rst/ref_$TAG/bp.mir ] || $S $A $REFLL -stop-after=block-placement -o $OUT/rst/ref_$TAG/bp.mir
$S $A rx/$n/m.ll -stop-after=block-placement -o $D/bp.mir || exit 1
python3 tools/blkrestore.py $D/bp.mir $OUT/rst/ref_$TAG/bp.mir $D/r.mir 2> $D/restore.txt
$S $A $D/r.mir -start-after=block-placement -filetype=obj -o $D/r.o || exit 1
python3 tools/sc.py $D/r.o | sed "s#^r.o#${n}_rst_$TAG#"
