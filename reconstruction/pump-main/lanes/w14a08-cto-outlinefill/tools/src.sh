#!/bin/bash
# src.sh <var> : raw IR capture (build slot) + opt -O3 + extracted llc + frame map  -> x/<var>/
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a08-cto-outlinefill; T=$O/tools; v=$1; w=${2:-work0}
OPT=~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/aarch64-apple-darwin/bin/opt; RB=$(dirname $OPT)
python3 $T/capraw.py $O/var/$v $O/$w $O/ir/$v > $O/ir/$v.log 2>&1 || { echo "$v capraw failed"; exit 1; }
[ -f $O/ir/$v/pump_recovered.raw.ll ] || { echo "$v no IR (compile error?)"; grep -m3 "^error" $O/ir/$v/build.log; exit 1; }
mkdir -p $O/o/$v; $OPT -O3 $O/ir/$v/pump_recovered.raw.ll -o $O/o/$v/opt.bc 2>$O/o/$v/opt.err
echo "$v $($T/xo.sh $O/o/$v/opt.bc $O/x/$v mir)"
$RB/llvm-dis $O/x/$v/ex.bc -o $O/x/$v/ex.ll; rm -f $O/o/$v/opt.bc
