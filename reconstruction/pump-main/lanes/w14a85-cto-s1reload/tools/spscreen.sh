#!/bin/bash
# spscreen.sh <base.ll> <tag> <vals file>
D=$(dirname $0); mkdir -p ~/.cache/pumpfun-reconstruction/lanes/w14a85-cto-s1reload/e/sp
xargs -P 4 -n 1 $D/sp1.sh $1 $2 < $3
