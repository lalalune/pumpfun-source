#!/bin/bash
# oracle.sh <raw.ll> <outdir> [extra opt args...] : opt -O3 + llc -> execute disasm (fn.txt), size, approx ratio vs original
set -e
RAW=$1; D=$2; shift 2
OPT=~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/aarch64-apple-darwin/bin/opt
B=~/.cache/solana/v1.44/platform-tools/llvm/bin
mkdir -p $D
$OPT -O3 "$@" $RAW -o $D/opt.bc 2> $D/opt.err
$B/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $D/opt.bc -filetype=obj -o $D/m.o 2> $D/llc.err
python3 $(dirname "$0")/objfn.py $D/m.o admin_cto7execute > $D/fn.txt
python3 $(dirname "$0")/oratio.py ${ORIG_FN:?set ORIG_FN to objfn.py output for the original window} $D/fn.txt
