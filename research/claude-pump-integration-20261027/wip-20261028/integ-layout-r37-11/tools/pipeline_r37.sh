#!/bin/bash
# pipeline_r37.sh <base crate dir (W/integ/r37g5/src)> <out crate dir> <out dir for the unpadded build> [--genuine-only]
# Rebuilds the integ-layout composite on the Round37 genuine base:
#   1. genuine source changes, in order:
#      coordfiles: tools/cf/structural37.py (S1-S6, S8; S7 skipped on Round37) then every other step listed in
#                  tools/cf/pipeline.sh (closures, split_buy_v2, closures2..8)
#      coordlib:   tools/cl/tools/restructure.py, tools/changes2_r37.py (section B), tools/cl/tools/changes3.py, changes4.py
#      nearmiss2:  tools/nm2_r37.py (validate_trade, add3/sub3, move_native, inline signer seeds)
#      g04-based lane deliveries listed in tools/g04_patches.txt (apply_lane_patches.py, after round3.py)
#      ext798:     tools/ext798.py (parallel Round37 frontier, shawkkkkk packets; NO_EXT798=1 skips)
#      round 4:    L06-based lane deliveries in tools/l06_patches.txt (apply_l06_patches.py: code-only, pads stripped)
#      integ lane: tools/integ_genuine.py (sell_quote helper; NO_INTEG=1 skips)
#      round 3:    tools/round3.py (pump-hi anchor-lang allow-missing-optionals, bodyloB-04 cumulative; NO_ROUND3=1 skips)
#   2. fastbuild of the unpadded crate (identity recipe) -> <out dir>/unstripped.so
#   3. SYNTHETIC line positioning, applied ONCE to the unpadded tree:
#      coordlib  tools/cl/layout.py apply --cand <unpadded build>                       (lib.rs only)
#      coordfiles: mksitemap.py from the unpadded build -> merge_sitemap.py (extra/integ anchors win for their windows)
#                  -> tools/cf/layout.py apply --sitemap merged --sitemap extra_anchors --sitemap integ_anchors (other files)
set -e
T=$(cd "$(dirname "$0")" && pwd)
W=/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work
rm -rf "$2"; cp -R "$1" "$2"
python3 $T/cf/structural37.py "$2" > /dev/null
for s in $(grep -oE 'python3 \$L/[a-z0-9_]+\.py "\$2"' $T/cf/pipeline.sh | sed -E 's/.*\$L\/([a-z0-9_]+)\.py.*/\1/' | grep -v '^layout$' | grep -v '^structural$'); do
  python3 $T/cf/$s.py "$2" > /dev/null; done
python3 $T/cl/tools/restructure.py "$2" > /dev/null
python3 $T/changes2_r37.py "$2" > /dev/null
python3 $T/cl/tools/changes3.py "$2" > /dev/null
python3 $T/cl/tools/changes4.py "$2" > /dev/null
python3 $T/nm2_r37.py "$2" > /dev/null
[ -n "$NO_ROUND3" ] || python3 $T/round3.py "$2" > /dev/null
G04=$(grep -v "^#" $T/g04_patches.txt 2>/dev/null | tr "\n" " "); [ -z "$G04" ] || python3 $T/apply_lane_patches.py "$2" $G04
[ -n "$NO_EXT798" ] || python3 $T/ext798.py "$2" > /dev/null
[ -n "$NO_INTEG" ] || python3 $T/integ_genuine.py "$2" > /dev/null
L06P=$(grep -v "^#" $T/l06_patches.txt 2>/dev/null | tr "\n" " "); [ -z "$L06P" ] || python3 $T/apply_l06_patches.py "$2" $L06P
[ "$4" = "--genuine-only" ] && { echo "genuine steps done: $2"; exit 0; }
mkdir -p "$3"
[ -f "$3/unstripped.so" ] || python3 $W/harness/fastbuild.py --src "$2" --work $W/lanes/integ-layout/work --out "$3" > "$3/fastbuild.out"
python3 $T/cl/layout.py apply --src "$2" --cand "$3/unstripped.so" | head -1
python3 $T/cf/mksitemap.py --src "$2" --cand "$3/unstripped.so" --pairs $T/cf/pairs.json --extra $T/cf/extra_anchors.json --out "$3/sitemap.json" | head -1
python3 $T/merge_sitemap.py "$3/sitemap.json" "$3/sitemap_merged.json" $T/cf/extra_anchors.json $T/integ_anchors.json
python3 $T/cf/layout.py apply --src "$2" --sitemap "$3/sitemap_merged.json" --sitemap $T/cf/extra_anchors.json --sitemap $T/integ_anchors.json | grep -E "OFF|FAIL" | grep -v SKIP || true
echo "pipeline done: $2 (build it with fastbuild.py and score with --baseline W/base/round37/inventory.json)"
