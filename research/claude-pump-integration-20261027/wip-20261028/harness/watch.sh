#!/bin/bash
W=/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work
R=/Users/shawwalters/Documents/Codex/2026-10-24/pumpfun-source
shopt -s nullglob
seen=$W/.watch-seen; touch $seen
last=$(git -C $R ls-tree --name-only origin/main repro/pump/ 2>/dev/null | grep -o 'round[0-9]*' | sort -V | tail -1)
n=0
while true; do
  for d in $W/deliveries/*/; do
    [ -f "$d/delivery.json" ] || continue
    if ! grep -qxF "$d" $seen; then echo "$d" >> $seen
      echo "DELIVERY $(basename $d): $(python3 -c "import json;d=json.load(open('$d/delivery.json'));print('norm',d.get('normalized'),'raw',d.get('raw'),'gains',len(d.get('gains',[])),'losses',len(d.get('losses',[])),'valid',d.get('runtime_valid'),'synthetic',d.get('synthetic_layout'))" 2>&1 | tail -1)"; fi
  done
  n=$((n+1))
  if [ $((n % 12)) -eq 0 ]; then git -C $R fetch -q origin 2>/dev/null
    r=$(git -C $R ls-tree --name-only origin/main repro/pump/ 2>/dev/null | grep -o 'round[0-9]*' | sort -V | tail -1)
    if [ -n "$r" ] && [ "$r" != "$last" ]; then echo "NEW CODEX ROUND on main: $r (was $last)"; last=$r; fi; fi
  sleep 10
done
