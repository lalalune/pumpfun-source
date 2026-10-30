#!/bin/bash
# rawedit.sh NAME EDIT.py : apply edit(text) to raw IR ($RAW), opt -O3, llc oracle; prints ratio lines + lea flag
O=~/.cache/pumpfun-reconstruction/lanes/w6r1-buyexactquote-ir; OPT=~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/aarch64-apple-darwin/bin/opt
n=$1; mkdir -p $O/rawexp
python3 - "$2" > $O/rawexp/$n.ll <<'PY'
import os,sys,runpy
ns=runpy.run_path(sys.argv[1]); t=open(os.environ.get('RAW',os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w6r1-buyexactquote-ir/out/raw-base/pump_recovered.ll'))).read()
t2=ns['edit'](t); assert t2!=t; print(t2)
PY
$OPT -O3 $O/rawexp/$n.ll -S -o $O/rawexp/$n.o3.ll && IRBASE=$O/rawexp/$n.o3.ll python3 $O/scripts/ir.py raw_$n - | tr '\n' ' '
echo " lea=$(sed -n 8p $O/irexp/raw_$n/fn.txt)"
[ -z "$KEEP" ] && rm -f $O/rawexp/$n.ll $O/rawexp/$n.o3.ll
