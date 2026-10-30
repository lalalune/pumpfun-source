#!/bin/bash
# mkc.sh name gene1 gene2 ... -> e/<name>.py combining genes
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a42-cto-entrycopy3; n=$1; shift
a=$(printf '"%s",' "$@"); printf 'exec(open("%s/e/common3.py").read())\nEDITS=GE(%s)\n' $O "${a%,}" > $O/e/$n.py; echo $n
