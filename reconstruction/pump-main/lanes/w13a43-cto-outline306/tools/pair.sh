#!/bin/bash
# pair.sh v... : run src.sh two at a time, then tsites
O=~/.cache/pumpfun-reconstruction/lanes/w13a43-cto-outline306; cd $O
set -- "$@"; while [ $# -gt 0 ]; do a=$1; b=$2; shift; [ -n "$b" ] && shift
 ./tools/src.sh $a work0 & [ -n "$b" ] && ./tools/src.sh $b work1 & wait
 python3 tools/tsites.py x/$a $( [ -n "$b" ] && echo x/$b )
done
