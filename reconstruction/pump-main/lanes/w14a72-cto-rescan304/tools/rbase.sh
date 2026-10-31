#!/bin/bash
# rbase.sh <name> [PAIRS]: rx m.ll of ir/<name>.ll already in rx/<name>/m.ll -> instnamer -> allclones -> rscan singles
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a72-cto-rescan304
N=$1; OPT=$(ls ~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/*/bin/opt)
$OPT -passes=instnamer rx/$N/m.ll -S -o ir/mn_$N.ll || exit 1
CL=$(python3 tools/allclones.py ir/mn_$N.ll | awk '{print $2}')
PAIRS=$PAIRS python3 tools/rscan.py ir/mn_$N.ll t/rs_$N.jsonl ${RT:-4} $CL
rm -f ir/mn_$N.ll
