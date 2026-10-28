#!/bin/bash
# Integrate one harvest onto the current frontier and stage a research packet for a PR.
# usage: [NEARMISS=1] integrate.sh HARVEST_DIR SLUG "Title" ["parent label"]
# Steps: compose (frontier + harvest src overlay) -> native build+measure -> Linux build -> relayout ordered.ld ->
#        2x Linux build (+ relayout --check) -> measure (asserts gain unless NEARMISS=1, never a loss) -> runtime
#        suites -> package_pr.py into the PR worktree -> packet verify. Stops at the first failure.
set -euo pipefail
RR=/Users/shawwalters/fees100-run
T=$RR/shared/tools
H=$(cd "$1" && pwd); SLUG=$2; TITLE=$3
FR=$(cat $RR/shared/frontier/CURRENT)
PARENT_LABEL=${4:-"the ${FR#w}-function Fees frontier"}
W=$RR/integration/$SLUG
mkdir -p $W
echo "[integrate] frontier=$FR harvest=$H work=$W"
rm -rf $W/src && cp -c -R $RR/shared/frontier/$FR $W/src
if [ -d "$H/src" ]; then (cd "$H/src" && find . -type f) | while read -r f; do mkdir -p "$W/src/$(dirname "$f")"; cp "$H/src/$f" "$W/src/$f"; done; fi
grep -q "anchor-attribute-program" $W/src/Cargo.toml
diff -ru $RR/shared/frontier/$FR $W/src > $W/compose.diff || true
echo "[integrate] composed; changed files:"; (grep '^diff -ru' $W/compose.diff | awk '{print $NF}' | sed "s|$W/src/||") || true
rm -rf $W/target-native; cp -c -R $RR/shared/target-native-warm $W/target-native 2>/dev/null || true
$T/nbuild.sh $W/src $W/target-native $W/native > /dev/null
(cd /tmp && python3 -I $T/measure.py $W/native-symbols.so --baseline $RR/shared/frontier/native/$FR-symbols.so --json $W/native-measure.json | head -1)
python3 -I $T/cbuild.py $W/src $W/linux0
python3 -I $T/relayout.py --old-ld $RR/shared/frontier/$FR/ordered.ld --old-map $RR/shared/frontier/container/$FR.map \
  --old-symbols $RR/shared/frontier/$FR-container-symbols.so --new-map $W/linux0.map --new-symbols $W/linux0-symbols.so \
  --out $W/ordered.relayout.ld --report $W/relayout.json
cp $W/ordered.relayout.ld $W/src/ordered.ld
python3 -I $T/cbuild.py $W/src $W/linux
python3 -I $T/cbuild.py $W/src $W/linux-repeat
python3 -I $T/relayout.py --check --old-ld $W/src/ordered.ld --new-map $W/linux.map
cmp $W/linux-symbols.so $W/linux-repeat-symbols.so && cmp $W/linux-candidate.so $W/linux-repeat-candidate.so && echo "[integrate] repeat build identical"
(cd /tmp && python3 -I $T/measure.py $W/linux-symbols.so --baseline $RR/shared/frontier/$FR-container-symbols.so --json $W/linux-measure.json | head -1)
python3 - "$W/linux-measure.json" <<'EOF'
import json, os, sys
d = json.load(open(sys.argv[1]))
assert not d['lost_normalized'], ('LOST normalized', d['lost_normalized'])
if os.environ.get('NEARMISS') != '1': assert d['gained_normalized'], 'no normalized gain on the Linux build'
if d['lost_raw']: print('WARNING raw lost (layout re-binding needed?):', d['lost_raw'][:20], len(d['lost_raw']))
print('[integrate] linux gained', d['gained_normalized'], 'normalized', d['normalized'], 'raw', d['raw_local'])
EOF
(cd /tmp && python3 -I $T/elfinv.py $W/linux-candidate.so --symbols $W/linux-symbols.so --json $W/elfinv.json --quiet > /dev/null) && python3 -c "import json; d=json.load(open('$W/elfinv.json')); print('[integrate] elfinv independent diffs:', len(d['B_independent']), 'equal_to_original:', d['candidate'].get('equal_to_original_extent'))"
(cd $RR/base && /Users/shawwalters/Documents/Codex/2026-10-24/pumpfun-source/work/test-env/bin/python scripts/fees_validate_all.py --candidate $W/linux-candidate.so --output $W/runtime.json > $W/runtime.log 2>&1) && tail -1 $W/runtime.log
cp "$H/NOTES.md" $W/NOTES.md
mkdir -p $RR/pr/research
python3 -I $T/package_pr.py --src $W/src --parent $RR/shared/frontier/$FR --parent-symbols $RR/shared/frontier/$FR-container-symbols.so \
  --parent-label "$PARENT_LABEL" --linux $W/linux --repeat $W/linux-repeat --runtime $W/runtime.json --notes $W/NOTES.md \
  --title "$TITLE" --out $RR/pr/research/claude-fees100-$SLUG-20261027 --repo $RR/base
(cd $RR/pr && python3 -B research/claude-fees100-$SLUG-20261027/verify.py | tail -12)
echo "[integrate] DONE packet=$RR/pr/research/claude-fees100-$SLUG-20261027"
