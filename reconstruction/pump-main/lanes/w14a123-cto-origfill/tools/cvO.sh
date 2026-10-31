#!/bin/bash
# cvO.sh <name> <genes> <slot>: cv.sh capture, then rx plain (name) and with 307/312 call-site noinline (name_O)
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a123-cto-origfill; cd $OUT
N=$1
bash tools/cv.sh "$@" >/dev/null 2>log_$N.err || { echo "$N compile-fail"; tail -3 log_$N.err; exit 1; }
python3 tools/rx.py ${N}_O ed/ni.py --base ir/$N.ll > /dev/null 2>&1
python3 tools/bfi.py ir/$N.ll | awk '$5==30||$5==19||$5==84{printf "%s:%s ",$5,$3}'; echo
python3 tools/fr.py $N ${N}_O
