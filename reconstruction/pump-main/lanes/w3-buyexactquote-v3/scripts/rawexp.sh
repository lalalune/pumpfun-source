#!/bin/bash
# rawexp.sh NAME "OPS" : reorder blocks in raw h01 IR, opt -O3, llc oracle
O=~/.cache/pumpfun-reconstruction/lanes/w3-buyexactquote-v3; OPT=~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/aarch64-apple-darwin/bin/opt
n=$1; mkdir -p $O/rawexp
IRBASE=$O/out/raw-h01/pump_recovered.ll OPS="$2" python3 - <<'PY' > $O/rawexp/$n.ll
import os,runpy
ns=runpy.run_path(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w3-buyexactquote-v3/iredits/reorder.py'))
t=open(os.environ['IRBASE']).read(); print(ns['edit'](t))
PY
$OPT -O3 $O/rawexp/$n.ll -S -o $O/rawexp/$n.o3.ll && IRBASE=$O/rawexp/$n.o3.ll python3 $O/scripts/ir.py raw_$n -
