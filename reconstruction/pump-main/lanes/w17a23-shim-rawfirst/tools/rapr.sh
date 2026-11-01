#!/bin/bash
# rapr.sh <name> <tag> [ENV=val ...]: private RAPRIO llc on fx/<name>/m.ll with env overrides; prints M/bytes via mj.py
set -u
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w17a23-shim-rawfirst
PL=$HOME/.cache/pumpfun-reconstruction/lanes/w16a20-cto-s3flagcolour/llvmb/bin/llc
n=$1; t=$2; shift 2
mkdir -p $OUT/rp
env "$@" nice -n 5 $PL -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $OUT/fx/$n/m.ll -filetype=obj -o $OUT/rp/$t.o 2>$OUT/rp/$t.err
python3 -c "
import sys; sys.path.insert(0,'$OUT/tools'); import oracle
b=oracle.elf_fn('$OUT/rp/$t.o',oracle.KEEP); open('$OUT/rp/$t.bin','wb').write(b)"
rm -f $OUT/rp/$t.o
LANE_OUT=$OUT python3 $OUT/tools/mj.py $OUT/rp/$t.bin
