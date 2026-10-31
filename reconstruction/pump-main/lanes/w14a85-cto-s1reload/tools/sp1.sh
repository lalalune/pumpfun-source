#!/bin/bash
# sp1.sh <base.ll> <tag> <%v>: one spillprobe + llcx score line
D=$(dirname $0); O=~/.cache/pumpfun-reconstruction/lanes/w14a85-cto-s1reload; B=$1; T=$2; v=$3
n="${T}_$(echo $v | tr -d '%.')"
python3 $D/spillprobe.py $B $O/e/sp/$n.ll $v >/dev/null 2>&1 || { echo "$v FAIL"; exit 0; }
r=$(python3 $D/llcx.py $n $O/e/sp/$n.ll | tail -1); echo "$v $r"; rm -f $O/e/sp/$n.ll; rm -rf $O/rx/$n
