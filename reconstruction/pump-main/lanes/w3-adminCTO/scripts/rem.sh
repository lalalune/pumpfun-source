#!/bin/zsh
# rem.sh <name>: inline remarks for admin_cto lines (to_string + others)
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w3-adminCTO
OUT=~/.cache/pumpfun-reconstruction/lanes/w3-adminCTO
export PUMP_BUILD_SLOTS=10
rsync -a --delete $WT/programs/pump/ $OUT/src/rem/
python3 $OUT/scripts/capture2.py $OUT/src/rem $OUT/work-rem $OUT/out/rem-$1 -Cremark=inline -Cdebuginfo=line-tables-only > $OUT/out/rem-$1.log 2>&1
grep "admin_cto.rs" $OUT/out/rem-$1/build.log | grep "to_string" | sed -E "s/note: programs[^:]*:([0-9]+):[0-9]+ inline \((success|missed)\).* into '([^']*)'.*(threshold=[0-9]+).*/\1 \2 \4 \3/" | sed -E 's/_ZN14pump_recovered9admin_cto7execute(8validate)?17h[0-9a-f]+E/\1/' | tr '\n' ';'
echo
