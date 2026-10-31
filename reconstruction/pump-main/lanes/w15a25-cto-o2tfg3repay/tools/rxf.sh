#!/bin/bash
# rxf.sh <name>: full oracle (opt -O3 + llc + score) on a kept capture ir/<name>.ll -> rxf.txt (inl map + fr tiers)
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a25-cto-o2tfg3repay; cd $OUT; N=$1
python3 tools/rx.py $N --base ir/$N.ll > /dev/null 2>&1
echo "$N | $(python3 tools/inl.py $N | cut -c14-) | $(python3 tools/ncall.py rx/$N/fn.bin | cut -d' ' -f2-) | $(python3 tools/fr.py $N | tr '\n' ' ') | $(cat rx/$N/res.json)" >> rxf.txt
rm -f rx/$N/m.o
