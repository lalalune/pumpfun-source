#!/bin/bash
# queue.sh <spec>...: run vscr.py on each spec in turn (2 workers), after any running vscr.py finishes
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a14-cto-vcretune/s16
while pgrep -f "vscr.py spec" >/dev/null; do sleep 10; done
for s in "$@"; do TAG=vc python3 vscr.py $s 2 > ${s%.txt}.log 2>&1; done
