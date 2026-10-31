#!/bin/bash
# restore.sh <variant m.ll> <out-prefix> <blocks> : MIR restore oracle (experiment only).
# Stops the variant before branch-folder, replaces "$r5 = COPY killed $r6" with the [r10-2264] reload in the listed
# bb56.i predecessors (pre-BF block numbers), resumes llc and scores. Round trip (no edit) is cmp-identical to llc.
O=~/.cache/pumpfun-reconstruction/lanes/w14a142-cto-holderflagtm; T=$O/tools
STOP=branch-folder $T/sb.sh "$1" $2.sbf.mir || exit 1
python3 $T/mired.py $2.sbf.mir $2.r.mir "$3" '$r5 = COPY killed $r6' '$r5 = LDD_V1 $r10, -2264'
$T/rt.sh $2.r.mir $2.r.o && python3 $T/wr.py $2.r.o
