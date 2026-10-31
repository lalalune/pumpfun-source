#!/bin/bash
# site.sh <name>: show the instructions after each 660 site Error::from call (stw 0x17cd)
D=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a111-cto-tag660
bash $D/tools/dis.sh ${PXD:-$D/px}/$1/m.o > $D/t/$1.dis
for n in $(grep -n "0x17cd" $D/t/$1.dis | cut -d: -f1); do
printf "  %s| " $(sed -n "${n}p" $D/t/$1.dis | awk '{print $1}')
sed -n "$((n+6)),$((n+11))p" $D/t/$1.dis | cut -f2- | grep -v '^$' | sed 's/^0000000000/@/' | tr '\n' ';'; echo; done
