#!/bin/bash
# asq.sh base.ll name moves... : moves -> llc asm -> block sequence from bb6.i (first 16)
M=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a112-cto-irorder14; SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin
b=$1; n=$2; shift 2
python3 $M/tools/mv2.py $b $M/io/$n.ll "$@" && $SDK/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $M/io/$n.ll -o $M/io/$n.s && python3 $M/seqt/seq.py $M/io/$n.s ${FROM:-bb6.i} ${NB:-16} | cut -c1-90
