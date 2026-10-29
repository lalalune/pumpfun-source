#!/bin/bash
O=~/.cache/pumpfun-reconstruction/lanes/w4-sellv3-phi
B=~/.cache/pumpfun-reconstruction/toolchains/hybrid144/rust/lib/rustlib/aarch64-apple-darwin/bin
export PUMP_BUILD_SLOTS=10
cd /tmp; python3 $O/tools/capture_pre.py $O/trials/$1 $O/ir/pre-$1 > $O/ir/pre-$1.log 2>&1
$B/llvm-dis $O/ir/pre-$1/pre.bc -o $O/ir/pre-$1/pre.ll
python3 $O/tools/unm.py $O/ir/pre-$1/pre.ll ${2:-5trade9sell_body17h}
