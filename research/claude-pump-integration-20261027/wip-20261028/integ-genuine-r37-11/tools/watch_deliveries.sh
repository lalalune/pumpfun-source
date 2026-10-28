#!/bin/bash
# watch_deliveries.sh: exits (printing the new names) as soon as W/deliveries has an entry not in work/deliveries.seen
# that is not one of ours (integ-*) and has a delivery.json; gives up after $1 seconds (default 1800).
W=/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work; S=$W/lanes/integ-layout/work/deliveries.seen
end=$(( $(date +%s) + ${1:-1800} ))
while [ $(date +%s) -lt $end ]; do
  new=$(ls $W/deliveries | sort | comm -13 $S - | grep -v '^integ-' | while read d; do [ -f $W/deliveries/$d/delivery.json ] && echo $d; done)
  if [ -n "$new" ]; then sleep 20; echo "NEW: $new"; exit 0; fi
  sleep 30
done
echo "timeout, nothing new"
