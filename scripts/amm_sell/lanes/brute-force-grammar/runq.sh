#!/bin/sh
# run list files sequentially: runq.sh a.json b.json ...
cd "$(dirname "$0")"
for f in "$@"; do python3 -B search.py list "$f" > "${f%.json}.log" 2>&1; done
