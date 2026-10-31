#!/bin/bash
# spn.sh <base.ll> <name> <%v1> [%v2 ...]: chained spillprobes, llcx score (keeps rx/<name>)
D=$(dirname $0); O=~/.cache/pumpfun-reconstruction/lanes/w14a85-cto-s1reload; B=$1; n=$2; shift 2
cp $B $O/e/sp/$n.0.ll; i=0
for v in "$@"; do python3 $D/spillprobe.py $O/e/sp/$n.$i.ll $O/e/sp/$n.$((i+1)).ll $v >/dev/null || { echo "$n FAIL $v"; exit 0; }; rm $O/e/sp/$n.$i.ll; i=$((i+1)); done
mv $O/e/sp/$n.$i.ll $O/e/sp/$n.ll
r=$(python3 $D/llcx.py $n $O/e/sp/$n.ll | tail -1); echo "$n $* :: $r"
