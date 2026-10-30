#!/bin/bash
# thr.sh <var> <variant> : thread2 on ir/<var> raw IR, opt, xo -> bw/thr_<var>_<variant>
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a07-cto-cold306; v=$1; t=$2; d=$O/bw/thr_${v}_$t; mkdir -p $d
OPT=~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/aarch64-apple-darwin/bin/opt
python3 $O/tools/thread2.py $O/ir/$v/pump_recovered.raw.ll $d/in.ll $t && $OPT -O3 $d/in.ll -o $d/opt.bc && echo "thr_${v}_$t $($O/tools/xo.sh $d/opt.bc $d)"; $(dirname $OPT)/llvm-dis $d/ex.bc -o $d/ex.ll; rm -f $d/in.ll $d/opt.bc; python3 $O/tools/tsites.py $d; python3 $O/tools/lseq.py $d/fn.txt 0x1c00
