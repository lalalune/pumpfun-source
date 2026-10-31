#!/bin/bash
# var.sh <name> <edit names...>: post-opt IR edits on rx/main/m.ll, score, layout diff vs main
O=~/.cache/pumpfun-reconstruction/lanes/w14a142-cto-holderflagtm; cd $O
N=$1; shift; E=(); for x in "$@"; do E+=("$O/e/ir/$x.py"); done
BASE=$O/rx/main/m.ll bash tools/pe.sh $N "${E[@]}" || exit 1
tools/l.sh pe/$N/m.ll /dev/null -print-after=block-placement 2> t/$N.pab.mir; python3 tools/lay.py t/$N.pab.mir > t/$N.lay
python3 tools/laydiff.py t/main.lay t/$N.lay | grep -v "^EQ" | head -${LD:-4} | cut -c1-200
