#!/bin/bash
# llco.sh <opt.ll> <outdir> : llc only + ratio
set -e
B=~/.cache/solana/v1.44/platform-tools/llvm/bin; T=$(dirname "$0"); mkdir -p $2
$B/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $1 -filetype=obj -o $2/m.o 2> $2/llc.err
python3 $T/objfn.py $2/m.o admin_cto7execute > $2/fn.txt
python3 $T/oratio.py $ORIG_FN $2/fn.txt
