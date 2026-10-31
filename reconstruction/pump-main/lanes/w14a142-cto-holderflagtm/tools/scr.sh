#!/bin/bash
# scr.sh "name e1 e2..." ... : var.sh each, plus join check (COPY count among bb56.i preds) and store-backs
O=~/.cache/pumpfun-reconstruction/lanes/w14a142-cto-holderflagtm; cd $O
for v in "$@"; do set -- $v; n=$1
  LD=${LD:-3} tools/var.sh "$@" 2>&1 | head -4
  STOP=branch-folder tools/sb.sh pe/$n/m.ll t/$n.sbf.mir 2>/dev/null && echo "  joinCOPY=$(python3 tools/jp.py t/$n.sbf.mir | grep -c COPY) $(python3 tools/fnx.py pe/$n/m.o t/$n.bin 2>/dev/null; true)"
done
