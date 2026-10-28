#!/bin/bash
# ci_pass.sh <NN unpadded> <NN padded> <prev genuine delivery> <prev layout delivery>
# One continuous-integration pass on r37g5: genuine pipeline -> build bNN1 -> both layout passes from that build -> build bNN2,
# then loss checks against the previous integ deliveries (normalized and raw windows).
set -e
W=/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work; L=$W/lanes/integ-layout; T=$L/tools
$T/pipeline_r37.sh $W/integ/r37g5/src $L/stage/ci$1 /dev/null --genuine-only > /dev/null
rm -rf $L/src; cp -R $L/stage/ci$1 $L/src
$T/bld.sh $1 | cut -c1-200
rm -rf $L/stage/ci$2 $L/stage/ci$2b; mkdir -p $L/stage/ci$2b; cp $L/builds/b$1/unstripped.so $L/stage/ci$2b/
$T/pipeline_r37.sh $W/integ/r37g5/src $L/stage/ci$2 $L/stage/ci$2b | grep -v "^pipeline done" | cut -c1-200
cp $L/stage/ci$2b/sitemap.json $L/work/sitemap_r37_b$1.json; cp $L/stage/ci$2b/sitemap_merged.json $L/work/sitemap_r37_b$1_merged.json
rm -rf $L/src; cp -R $L/stage/ci$2 $L/src
$T/bld.sh $2 | cut -c1-200
python3 - $L/builds/b$1 $L/builds/b$2 $W/deliveries/$3 $W/deliveries/$4 <<'PY'
import json, sys
def w(p): return json.load(open(p + '/score.json'))['windows']
for cur, prev in [(sys.argv[1], sys.argv[3]), (sys.argv[2], sys.argv[4])]:
    c, p = w(cur), w(prev)
    gain = [hex(int(k)) for k, v in c.items() if v['normalized'] and not p[k]['normalized']]
    lost = [hex(int(k)) for k, v in c.items() if not v['normalized'] and p[k]['normalized']]
    rlost = [hex(int(k)) for k, v in c.items() if not v['raw'] and p[k]['raw']]
    n = sum(v['normalized'] for v in c.values()); r = sum(v['raw'] for v in c.values())
    print(f"{cur.split('/')[-1]}: {n}/{r} vs {prev.split('/')[-1]}: +{gain} LOST {lost} RAW-LOST {rlost}")
PY
