#!/bin/bash
# mkann.sh <unstripped.so> <out_ann.txt> : annotated admin_cto::execute listing
B=~/.cache/solana/v1.44/platform-tools/llvm/bin; T=$(dirname "$0")
SO=$1; O=$2
$B/llvm-readelf -sW --demangle $SO | awk '$4=="FUNC"{n=$8; for(i=9;i<=NF;i++) n=n" "$i; print $2, $3, n}' > $O.syms
L=$($B/llvm-readelf -sW $SO | awk '$4=="FUNC" && $8 ~ /admin_cto7execute/ {print $2, $3; exit}')
A=$(echo $L | awk '{print $1}'); N=$(echo $L | awk '{print $2}')
python3 $T/ann.py $SO $O.syms $A $N > $O
echo "start 0x$A bytes $N"
