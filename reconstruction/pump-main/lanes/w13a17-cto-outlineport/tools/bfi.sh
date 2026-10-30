#!/bin/bash
# bfi.sh <var> [work] : validate's pre-inliner block frequencies at each to_string site (cold < 0.02)
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a17-cto-outlineport; v=$1; w=${2:-work0}
OPT=~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/aarch64-apple-darwin/bin/opt; D=$O/ir/b_$v; mkdir -p $D
[ -f $D/pump_recovered.raw.ll ] || python3 $O/tools/capraw.py $O/var/$v $O/$w $D > $D.log 2>&1
V=$(grep -o "^define[^@]*@_ZN14pump_recovered9admin_cto8validate[A-Za-z0-9_]*" $D/pump_recovered.raw.ll | sed 's/.*@//')
$OPT -O3 -print-before=inline -print-module-scope -filter-print-funcs=$V $D/pump_recovered.raw.ll -o /dev/null 2> $D/premod.txt
tail -n +2 $D/premod.txt > $D/premod.ll; rm $D/premod.txt
$OPT -passes='print<block-freq>' -disable-output $D/premod.ll 2> $D/bfi_all.txt
python3 - $D $V <<'PY'
import sys,re
D,V=sys.argv[1:3]; t=open(D+'/bfi_all.txt').read(); i=t.find("block-frequency-info: "+V); j=t.find("block-frequency-info:",i+10); open(D+'/bfi_val.txt','w').write(t[i:j])
L=open(D+'/premod.ll').read().split('\n'); s=next(k for k,l in enumerate(L) if l.startswith('define') and V in l); e=next(k for k in range(s,len(L)) if L[k]=='}')
open(D+'/prein.txt','w').write('\n'.join(L[s:e+1]))
PY
python3 $O/tools/bfisites.py $D/prein.txt $D/bfi_val.txt | tr '\n' ';'; echo; rm -f $D/premod.ll $D/bfi_all.txt
